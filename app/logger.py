import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def get_db_logger() -> logging.Logger:
    logger = logging.getLogger("app.logger.database")
    logger.setLevel(logging.WARNING)

    if not logger.hasHandlers():
        handler = TimedRotatingFileHandler(
            filename=LOG_DIR / "db_errors.log",
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

db_logger = get_db_logger()
