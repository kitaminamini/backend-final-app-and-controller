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


@sio.on('status', namespace="/")
async def status(sid, msg):
    logger.info("user: {} joined status event".format(sid))
    # go to mongo and check if the status already exist and tell where the packing is at
    bucket_name, object_name = msg.split("/")
    query = {'bucket_name': bucket_name,
             'object_name': object_name}
    result = mongo.collection.find_one(query)
    if result is not None and "num_pdf" in result:
        pdf_count = result["num_pdf"]
        txt_count = result["num_txt"]
        if result["packed"]:
            await sio.emit('listen_status', room=sid, data="packed")
        elif pdf_count == 0:
            await sio.emit('listen_status', room=sid, data="unpacking")
        elif pdf_count == txt_count:
            await sio.emit('listen_status', room=sid, data="packing")
        else:
            await sio.emit('listen_status', room=sid, data="{}/{}".format(txt_count, pdf_count))


@sio.on('join', namespace="/")
def join(sid, message):
    logger.info("user: {} coming in".format(sid))
    if message not in upload_dict.keys():
        upload_dict[message] = set()
    if message != '':
        logger.info("user: {}, listening to: {}".format(sid, message))
    upload_dict[message].add(sid)
    user_dict[sid] = message
    logger.info("user: {} joined event".format(sid))


@sio.on('leave', namespace="/")
def leave(sid):
    upload_dict.pop(user_dict[sid])
    user_dict.pop(sid)
    sio.disconnect(sid)
    logger.info("user: {} leave event".format(sid))


# Update num_txt and check if all pdf converted
async def check_is_convert_done(bucket_name, object_name, pdf_name):
    col = mongo.collection
    query = {'bucket_name': bucket_name,
             'object_name': object_name}
    update_param = {"$inc": {"num_txt": 1}}
    col.update_one(query, update_param)
    counts = col.find_one(query)
    if counts is None:
        # should not hit ever but i'm not taking chances
        return
    logger.info("counts: {}".format(counts))
    pdf_count = counts["num_pdf"]
    txt_count = counts["num_txt"]
    if pdf_count == txt_count:
        publish(bucket_name, object_name, pdf_name)
    logger.info("check is convert done: bucket_name: {}, object_name: {}".format(bucket_name, object_name))
    if bucket_name + "/" + object_name in upload_dict.keys():
        sids = upload_dict[bucket_name + "/" + object_name]
        for sid in sids:
            logger.info("sending status to {}".format(sid))
            if pdf_count == txt_count:
                await sio.emit('listen_status', room=sid, data="packing")
            else:
                await sio.emit('listen_status', room=sid, data="{}/{}".format(txt_count, pdf_count))


def publish(bucket_name, object_name, pdf_name):
    json_dic = {"bucket_name": bucket_name,
                "object_name": object_name,
                "pdf_name": pdf_name}
    msg = json.dumps(json_dic)
    rmq.publish(msg, "rmq4")


async def status_callback(message: aio_pika.IncomingMessage):
    ## json format:
    # { bucket_name: string
    # object_name: string
    # pdf_name: string }
    with message.process():
        body = message.body
        json_body = json.loads(body)
        bucket_name = json_body["bucket_name"]
        object_name = json_body["object_name"]
        pdf_name = json_body["pdf_name"]
        if object_name.startswith('pack-') and pdf_name == "":
            if bucket_name + "/" + object_name[5:] in upload_dict.keys():
                sids = upload_dict[bucket_name + "/" + object_name[5:]]
                logger.info("Sending packed status")
                for sid in sids:
                    logger.info("Sending status to {}".format(sid))
                    await sio.emit("listen_status", room=sid, data="packed")
            else:
                logger.info("no user is listening to status {}".format(bucket_name + "/" + object_name[5:]))
        else:
            await check_is_convert_done(bucket_name, object_name, pdf_name)


_Handler = socketio.get_tornado_handler(sio)


class SocketHandler(_Handler):
    def check_origin(self, origin):
        return True


async def make_app(config):
    logger.info("connecting to rabbit mq")

    queue_name = "rmq3"
    connected = False
    start = int(time.time() * 1000.0)
    current = int(time.time() * 1000.0)
    while not connected and current - start < 30000:
        try:
            connection = await aio_pika.connect_robust(
                "amqp://guest:guest@{}:{}/".format(config["host"], config["port"]),
                loop=io_loop.asyncio_loop)
            channel = await connection.channel()  # type: aio_pika.Channel
            logger.info("Exchange info: name {}".format(config["exchanges"][queue_name]),)
            await channel.declare_exchange(config["exchanges"][queue_name],
                                           type=aio_pika.ExchangeType.FANOUT)
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
    # application = Application([
    #     (r"/([a-zA-Z0-9]+)/(.+)", FileHandler),
    #     (r"/([a-zA-Z0-9]+)", BucketHandler),
    #     (r"/socket.io/", SocketHandler)
    # ], debug=True)
    logger.info("making application")
    app = io_loop.asyncio_loop.run_until_complete(make_app(config["rabbitmq"]))
    logger.info("finish making application")
    app.listen(config["web_controller"]["port"])
    logger.info("starting application")
    tornado.ioloop.IOLoop.current().start()

