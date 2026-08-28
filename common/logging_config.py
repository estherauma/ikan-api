import os

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def build_logging_config():
    log_dir = os.path.join(BASE_DIR, "logs")

    os.makedirs(log_dir, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "daily_file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "verbose",
                "filename": os.path.join(log_dir, "app.log"),
                "when": "midnight",
                "interval": 1,
                "backupCount": 30,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "daily_file"],
            "level": 'INFO',
        },
        "loggers": {
            "django.utils.autoreload": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "matplotlib": {
                "handlers": ["console", "daily_file"],
                "level": "ERROR",
                "propagate": False,
            },
            "matplotlib.font_manager": {
                "handlers": ["console", "daily_file"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }
