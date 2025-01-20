import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging(level=logging.INFO):

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.getLogger()
    logger.setLevel(level)

    file_handler = RotatingFileHandler(
        filename=os.getenv("LOG_FILE", "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setFormatter(logging.Formatter(log_format))

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
