import os
from logging.config import dictConfig

from dotenv import load_dotenv

load_dotenv(override=True)  # Load environment variables from .env file

MANAGEMENT_DATABASE_URL = os.getenv("MANAGEMENT_DATABASE_URL")
MANAGEMENT_DATABASE_URL_SYNC = os.getenv("MANAGEMENT_DATABASE_URL_SYNC")
TENANT_DATABASE_TEMPLATE_URL = os.getenv("TENANT_DATABASE_TEMPLATE_URL")  # Template URL for tenant databases
ADMIN_DOMAIN = os.getenv("ADMIN_DOMAIN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
ADMIN_HOST = os.getenv("ADMIN_HOST")
ADMIN_PORT = os.getenv("ADMIN_PORT")
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
DISABLE_CAPTCHA = True  # os.getenv("DISABLE_CAPTCHA", "False").lower() in ("true", "1", "t")


def setup_logging():
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            },
            "detailed": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s (%(pathname)s:%(lineno)d)",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
            "file": {
                "level": "DEBUG",
                "class": "logging.FileHandler",
                "filename": "app.log",
                "formatter": "detailed",
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
        },
        "loggers": {
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    }

    dictConfig(logging_config)
