from tornado.web import *
from module.utility import *
from module.miniodao import *
from module.mongodao import *
from module.rabbitmqdao import *
import hashlib
import json
from minio.error import *
import io
import asyncio
import aio_pika



class Singleton:
    config = get_config()
    mongo = MongoDAO(config["mongo"])
    rabbit = RabbitMQDAO(config["rabbitmq"])
    minio = MinioDAO(config["minio"])


# singleton for all
singleton = Singleton()
logger = logging.getLogger(__name__)


    # application = tornado.web.Application([
    #   (r"/articles", ArticleHandler),])
class ArticleHandler(RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    # Default: 
    # Filter by: topics, rss  
    # Required query: num=
    def get(self):
        self.set_default_headers()
        num = self.get_argument('num', None)
        topics = self.get_argument('topics', None)
        rss = self.get_argument('rss', None)
        if topics!=None and rss!=None:

        elif topics!=None:

        elif rss!=None: 

        else:

        # if not singleton.minio.client.bucket_exists(bucket_name):
        #     raise HTTPError(404)
        # try:
        #     singleton.minio.client.stat_object(bucket_name, object_name)
        # except FileNotFoundError:
        #     logger.info("File did not exist in minio, proceeding to do the unpacking process.")
        #     raise HTTPError(404)
        # except Exception as err:
        #     logger.error(str(err))
        #     raise HTTPError(404)
        # data = singleton.minio.client.get_object(bucket_name, object_name)
        # stat = singleton.minio.client.stat_object(bucket_name, object_name)
        # self.set_header('Content-Disposition', 'attachment; filename={}'.format(object_name))
        # self.set_header('Content-Transfer-Encoding', 'binary')
        # self.set_header("Content-Length", stat.size)
        # for d in data.stream(32*1024):
        #     self.write(d)
        self.finish()

    # upload the tar ball to be converted
    # get bucketname objectname
    # check if bucketname exists, create if u have to, else proceed next
    # if above condition filled, check if object is inside
    # object_name must be .tar.gz
    async def post(self, bucket_name, object_name):
        self.set_default_headers()
        # singleton.minio.client.bucket_exists()
        logger.debug("bucket_name: {}, object_name: {}".format(bucket_name, object_name))
        try:
            exists = singleton.minio.client.bucket_exists(bucket_name)
            logger.debug("exists: {}".format(exists))
            if not exists:
                singleton.minio.client.make_bucket(bucket_name)
        except Exception as err:
            logger.error("error: {}".format(err))
            raise HTTPError(500)

        object_hash = hashlib.md5(self.request.body).hexdigest()
        object_name = object_hash + "-" + object_name
        found = False
        logger.debug("bucket_name: {}, object_name: {}, hash: {}".format(bucket_name, object_name, object_hash))
        try:
            singleton.minio.client.stat_object(bucket_name, object_name)
            found = True
        except NoSuchKey:
            logger.info("File did not exist in minio, proceeding to do the unpacking process.")
        except Exception as err:
            logger.error("error: " + str(err))
            raise HTTPError(404)
        if found:
            # return the object back from minio
            self.write(json.dumps({
                "output_name": "pack-" + object_name
            }))
            self.finish()
            return
        else:
            
        singleton.mongo.collection.insert_one({
            "bucket_name": bucket_name,
            "object_name": object_name,
            "output_name": "pack-" + object_name,
            "hash": object_hash,
            "num_txt": 0,
            "packed": False,
        })
        rmq1_msg = json.dumps({
            "bucket_name": bucket_name,
            "object_name": object_name,
            "hash": object_hash
        })

        connection = self.application.settings['amqp_connection']
        channel: aio_pika.Channel = await connection.channel()
        try:
            exchange: aio_pika.Exchange = await channel.declare_exchange(singleton.config["rabbitmq"]["exchanges"]["rmq1"],
                                                                         type=aio_pika.ExchangeType.FANOUT)
            logger.info("---------declaring queue ---------")
            await channel.declare_queue(singleton.config["rabbitmq"]["rmq1"])
            logger.info("---------sending msg---------")
            await exchange.publish(aio_pika.Message(body=bytes(rmq1_msg, 'utf-8')),
                                   routing_key=singleton.config["rabbitmq"]["rmq1"])
            logger.info("---------after publish---------")
        except Exception as err:
            logger.error("=======ERROR: {}========".format(err))
            raise HTTPError(500)
        finally:
            await channel.close()
        self.write(json.dumps({
            "output_name": "pack-"+object_name,
            "object_name": object_name,
        }))
        self.finish()


    def options(self, *args, **kwargs):
        self.set_default_headers()
        self.set_status(200)

    def data_received(self, chunk):
        pass

    # application = tornado.web.Application([
    #   (r"/topics", TopicHandler),])
class TopicHandler(RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self, topics):
        self.set_default_headers()
        query = {"$or": [{"topic": t} for t in topics]}
        col = singleton.mongo.collection
        results = col.find(query)
        ret = []
        if results is not None:
            for result in results:
                result["_id"] = str(result["_id"])
                ret.append(result)
        if len(ret) == 0:
            self.write("")
        else:
            self.write(json.dumps(ret))
        self.finish()

    def post(self, *args, **kwargs):
        self.set_default_headers()
        self.set_status(200)

    def options(self, *args, **kwargs):
        self.set_default_headers()
        self.set_status(200)

    def data_received(self, chunk):
        pass

    # application = tornado.web.Application([
    #   (r"/rss", RssHandler),])
class RssHandler(RequestHandler):

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def check_origin(self, origin):
        return True

    def get(self, rss):
        self.set_default_headers()
        query = {"$or": [{"rss": r} for r in rss]}
        col = singleton.mongo.collection
        results = col.find(query)
        ret = []
        if results is not None:
            for result in results:
                result["_id"] = str(result["_id"])
                ret.append(result)
        if len(ret) == 0:
            self.write("")
        else:
            self.write(json.dumps(ret))
        self.finish()

    async def post(self, rss):
        self.set_default_headers()
        doc = {"rss": rss}
        col = singleton.mongo.collection
        results = col.insert_one(doc)

        rmq1_msg = json.dumps(doc)

        connection = self.application.settings['amqp_connection']
        channel: aio_pika.Channel = await connection.channel()
        try:
            exchange: aio_pika.Exchange = await channel.declare_exchange(singleton.config["rabbitmq"]["exchanges"]["rmq1"],
                                                                         type=aio_pika.ExchangeType.FANOUT)
            logger.info("---------declaring queue ---------")
            await channel.declare_queue(singleton.config["rabbitmq"]["rmq1"])
            logger.info("---------sending msg---------")
            await exchange.publish(aio_pika.Message(body=bytes(rmq1_msg, 'utf-8')),
                                   routing_key=singleton.config["rabbitmq"]["rmq1"])
            logger.info("---------after publish---------")
        except Exception as err:
            logger.error("=======ERROR: {}========".format(err))
            raise HTTPError(500)
        finally:
            await channel.close()
        self.write(json.dumps({
            "output_name": "pack-"+object_name,
            "object_name": object_name,
        }))

        self.set_status(200)
        self.finish()

    def options(self, *args, **kwargs):
        self.set_default_headers()
        self.set_status(200)

    def data_received(self, chunk):
        pass