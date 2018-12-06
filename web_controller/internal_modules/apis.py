from tornado.web import *
from module.utility import *
from module.mongodao import *
from module.rabbitmqdao import *
import hashlib
import json
import io
import asyncio
import aio_pika



class Singleton:
    config = get_config()
    mongo = MongoDAO(config["mongo"])
    rabbit = RabbitMQDAO(config["rabbitmq"])



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
        if num == None:
            self.set_status(400)

        else:
            # query = {"$limit": int(num)}
            db = singleton.mongo.client["results"]
            col = db["results"]
            results = col.find({}).sort([("_id", -1)]).limit(int(num))
            ret = []
            if results is not None:
                for result in results:
                    result["_id"] = str(result["_id"])
                    ret.append(result)
            self.set_status(200)
            self.write(json.dumps({"articles": ret}))

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

    def get(self):
        self.set_default_headers()
        topics = self.get_argument('topics', None)
        labels = [t for t in topics.split(',')]
        logger.info(labels)
        query = {"label": {"$in": labels}}
        db = singleton.mongo.client["results"]
        col = db["results"]
        results = col.find(query)
        ret = []
        if results is not None:
            for result in results:
                result["_id"] = str(result["_id"])
                ret.append(result)
        self.set_status(200)
        self.write(json.dumps({"articles": ret}))
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

    def get(self):
        self.set_default_headers()
        rss = num = self.get_argument('rss', None)
        query = {"rss": rss}
        db = singleton.mongo.client["results"]
        col = db["results"]
        results = col.find(query)
        ret = []
        if results is not None:
            for result in results:
                result["_id"] = str(result["_id"])
                ret.append(result)
        self.set_status(200)
        self.write(json.dumps({"articles": ret}))
        self.finish()

    async def post(self):
        self.set_default_headers()
        body = self.request.body
        json_body = json.loads(body)
        rss = json_body["rss"]

        connection = self.application.settings['amqp_connection']
        channel: aio_pika.Channel = await connection.channel()
        try:
            logger.info("---------declaring queue ---------")
            await channel.declare_queue(singleton.config["rabbitmq"]["rss"])
            logger.info("---------sending msg---------")
            await channel.default_exchange.publish(aio_pika.Message(body=bytes(rss, 'utf-8')),
                                   routing_key=singleton.config["rabbitmq"]["rss"])
            logger.info("---------after publish---------")
        except Exception as err:
            logger.error("=======ERROR: {}========".format(err))
            raise HTTPError(500)
        finally:
            await channel.close()

        self.set_status(200)
        self.write(rss)
        
        self.finish()

    def options(self, *args, **kwargs):
        self.set_default_headers()
        self.set_status(200)

    def data_received(self, chunk):
        pass