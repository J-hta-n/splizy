import logging


def get_logger(name: str = "ptb-bot") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
        )
    return logger
