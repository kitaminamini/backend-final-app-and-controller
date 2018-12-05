from minio import Minio
import time
import logging


class MinioDAO:

    def __init__(self, config, logger=None):
        self.config = config
        connected = False
        start = int(time.time() * 1000.0)
        current = int(time.time() * 1000.0)
        self.logger = logger or logging.getLogger(__name__)
        while not connected and current - start < 30000:
            try:
                self.client = Minio(config["host"] + ":" + str(config["port"]),
                                    access_key=config["access_key"],
                                    secret_key=config["secret_key"],
                                    secure=False)
                connected = True
            except Exception as err:
                self.logger.info("error: {}".format(err))
        if not connected:
            raise ConnectionError
