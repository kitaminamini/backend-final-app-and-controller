import logging
import pika
import time


class RabbitMQDAO:

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def publish(self, msg, queue):
        connection = None
        connected = False
        start = int(time.time()*1000.0)
        current = int(time.time()*1000.0)
        while not connected and current - start < 30000:
            try:
                current = int(time.time()*1000.0)
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=self.config["host"],
                    port=self.config["port"]))
                connected = True
                channel = connection.channel()
                channel.queue_declare(queue=self.config[queue])
                channel.exchange_declare(exchange=self.config["exchanges"][queue],
                                         exchange_type='fanout')
                channel.queue_bind(exchange=self.config["exchanges"][queue],
                                   queue=self.config[queue])
                channel.basic_publish(exchange=self.config["exchanges"][queue],
                                      routing_key=self.config[queue],
                                      body=msg)
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                time.sleep(6)
            finally:
                if connection:
                    connection.close()
        if not connected:
            raise ConnectionError

    def listen(self, queue, callback):
        connection = None
        connected = False
        start = int(time.time()*1000.0)
        current = int(time.time()*1000.0)
        while not connected and current-start < 30000:
            try:
                current = int(time.time()*1000.0)
                connection = pika.BlockingConnection(pika.ConnectionParameters(
                    host=self.config["host"],
                    port=self.config["port"]))
                connected = True
                channel = connection.channel()
                channel.exchange_declare(exchange=self.config["exchanges"][queue],
                                         exchange_type='fanout')
                channel.queue_declare(queue=self.config[queue])
                channel.queue_bind(exchange=self.config["exchanges"][queue],
                                   queue=self.config[queue])
                channel.basic_consume(callback,
                                      queue=self.config[queue],
                                      no_ack=True)
                channel.start_consuming()
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                time.sleep(6)
            finally:
                if connection:
                    connection.close()
        if not connected:
            raise ConnectionError

