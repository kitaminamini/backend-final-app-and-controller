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
        # if len(ret) == 0:
        #     self.write("")
        # else:
        self.write(json.dumps({"articles": ret}))
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
            # exchange: aio_pika.Exchange = await channel.declare_exchange(singleton.config["rabbitmq"]["exchanges"]["rmq1"],
            #                                                              type=aio_pika.ExchangeType.FANOUT)
            logger.info("---------declaring queue ---------")
            await channel.declare_queue(singleton.config["rabbitmq"]["rss"])
            logger.info("---------sending msg---------")
            await exchange.publish(aio_pika.Message(body=bytes(rmq1_msg, 'utf-8')),
                                   routing_key=singleton.config["rabbitmq"]["rss"])
            logger.info("---------after publish---------")
        except Exception as err:
            logger.error("=======ERROR: {}========".format(err))
            raise HTTPError(500)
        finally:
            await channel.close()

        self.write(rmq1_msg)

        self.set_status(200)
        self.finish()

    def options(self, *args, **kwargs):
        self.set_default_headers()
        self.set_status(200)

    def data_received(self, chunk):
        pass