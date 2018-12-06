import os


def get_config():
    return {
        "web_controller": {
            "host": os.environ.get("WEB_CONTROLLER", "localhost"),
            "port": int(os.environ.get("WEB_CONTROLLER_SERVICE_PORT", "8000")),
        },
        "job_dispatcher": {
            "host": os.environ.get("JOB_DISPATCHER", "localhost"),
            "port": int(os.environ.get("JOB_DISPATCHER_SERVICE_PORT", "8001")),
        },
        "converter": {
            "host": os.environ.get("CONVERTER", "localhost"),
            "port": int(os.environ.get("CONVERTER_SERVICE_PORT", "8002")),
        },
        "packer": {
            "host": os.environ.get("PACKER", "localhost"),
            "port": int(os.environ.get("PACKER_SERVICE_PORT", "8003")),
        },
        "status": {
            "host": os.environ.get("STATUS", "localhost"),
            "port": int(os.environ.get("STATUS_SERVICE_PORT", "8004")),
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
            "rmq2": "rmq2",
            "rmq3": "rmq3",
            "status": "status"
        },
        "minio": {
            "host": os.environ.get("MINIO", "localhost"),
            "port": int(os.environ.get("MINIO_SERVICE_PORT", "9000")),
            "access_key": os.environ.get("MINIO_ACCESS_KEY", "access_key"),
            "secret_key": os.environ.get("MINIO_SECRET_KEY", "secret_key"),
        }
    }
