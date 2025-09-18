from loguru import logger
import sys


def configure_logging() -> None:
    logger.remove()
    logger.add(sys.stdout, level="INFO", enqueue=True, backtrace=False, diagnose=False,
               format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}")
