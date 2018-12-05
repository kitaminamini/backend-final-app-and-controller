import logging
import pymongo
import time


class MongoDAO:

    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.logger.debug("Initialize Mongo: config: {}".format(config))
        connected = False
        start = int(time.time()*1000.0)
        current = int(time.time()*1000.0)
        while not connected and current - start < 30000:
            try:
                current = int(time.time()*1000.0)
                self.client = pymongo.MongoClient(host=config["host"], port=config["port"])
                self.database = self.client[config["database"]]
                self.collection = self.database[config["collection"]]
                connected = True
            except Exception as err:
                self.logger.error("Error: {0}".format(err))
                time.sleep(6)
        if not connected:
            raise ConnectionError
        self.logger.debug("Successfully Initialize Mongo")
