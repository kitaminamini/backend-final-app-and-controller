import tornado.ioloop
import module.utility
from internal_modules.apis import *
import socketio
from module.miniodao import MinioDAO
from module.rabbitmqdao import RabbitMQDAO
from module.mongodao import MongoDAO
import json
import aio_pika
import asyncio
import time


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
info_handler = logging.FileHandler('server_info.log')
info_handler.setLevel(logging.INFO)
debug_handler = logging.FileHandler('debug.log')
debug_handler.setLevel(logging.DEBUG)
warn_handler = logging.FileHandler('server_warn.log')
warn_handler.setLevel(logging.WARN)
error_handler = logging.FileHandler('server_error.log')
error_handler.setLevel(logging.ERROR)
sio = socketio.AsyncServer(async_mode='tornado')
config = module.utility.get_config()
rmq = RabbitMQDAO(config["rabbitmq"])
minio = MinioDAO(config["minio"])
mongo = MongoDAO(config["mongo"])
upload_dict = dict()
user_dict = dict()
tornado.ioloop.IOLoop.configure('tornado.platform.asyncio.AsyncIOLoop')
io_loop = tornado.ioloop.IOLoop.current()
asyncio.set_event_loop(io_loop.asyncio_loop)


async def status_callback(message: aio_pika.IncomingMessage):
    with message.process():
        body = message.body
        json_body = json.loads(body)
        status = json_body["status"]
        if status != "OK":
            report = {"newData": False}
            sio.emit(json.dumps(report))
            # report status and msg to frontend

        else:
            report = {"newData": True}
            sio.emit(json.dumps(report))



_Handler = socketio.get_tornado_handler(sio)


class SocketHandler(_Handler):
    def check_origin(self, origin):
        return True


async def make_app(config):
    logger.info("connecting to rabbit mq")

    queue_name = "status"
    connected = False
    start = int(time.time() * 1000.0)
    current = int(time.time() * 1000.0)
    while not connected and current - start < 30000:
        try:
            connection = await aio_pika.connect_robust(
                "amqp://guest:guest@{}:{}/".format(config["host"], config["port"]),
                loop=io_loop.asyncio_loop)
            channel = await connection.channel()  # type: aio_pika.Channel
            # logger.info("Exchange info: name {}".format(config["exchanges"][queue_name]),)
            # await channel.declare_exchange(config["exchanges"][queue_name],
            #                                type=aio_pika.ExchangeType.FANOUT)
            queue = await channel.declare_queue(config[queue_name])  # type: aio_pika.Queue
            connected = True
            logger.info("successfully connect to rabbit mq")
        except Exception as err:
            logger.error("Error: {0}".format(err))
            time.sleep(6)
    if not connected:
        raise ConnectionError

    # Declaring queue
    logger.info("starting async slisten to rabbit mq")
    # async for message in queue:
    #     with message.process():
    #         # print(message.body)
    #         logger.info("message: {}".format(message.body))
    #         status_callback('', '', '', message.body)
    #         if queue.name in message.body.decode():
    #             break
    await queue.consume(status_callback)
    return tornado.web.Application(
        [
            (r"/articles", ArticleHandler),
            (r"/topics", TopicHandler),
            (r"/rss", RssHandler)
        ],
        amqp_connection=connection,
        debug=True
    )


if __name__ == "__main__":
    config = module.utility.get_config()
    logger.info("Starting application")

    logger.info("making application")
    app = io_loop.asyncio_loop.run_until_complete(make_app(config["rabbitmq"]))
    logger.info("finish making application")
    app.listen(config["web_controller"]["port"])
    logger.info("starting application")
    tornado.ioloop.IOLoop.current().start()


