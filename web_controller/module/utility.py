import os


def get_config():
    return {
        "web_controller": {
            "host": os.environ.get("WEB_CONTROLLER", "localhost"),
            "port": int(os.environ.get("WEB_CONTROLLER_SERVICE_PORT", "8000")),
        },
        "mongo": {
            "host": os.environ.get("MONGO", "localhost"),
            "port": int(os.environ.get("MONGO_SERVICE_PORT", "27017")),
            "database": "results",
            "collection": "results",
            # {_id: ObjectId, title: string, rss: string, labels: List[String]}
        },
        "rabbitmq": {
            "host": os.environ.get("RABBITMQ", "localhost"),
            "port": int(os.environ.get("RABBITMQ_SERVICE_PORT", "5672")),
            "rss": "rss",
            "status": "status",
            "exchanges": {
                "rss": "r1"
            }
        }
    }
