import logging
import sys
from dataclasses import dataclass

from notifiers.logging import NotificationHandler

NOTICE = logging.ERROR


@dataclass
class TelegramNotificationConfig:
    token: str
    chat_id: str


@dataclass
class Config:
    filename: str
    telegram: TelegramNotificationConfig


class MyLogger(logging.Logger):
    def __init__(self, name: str, level: int | str = 0) -> None:
        super().__init__(name, level)

    def notice(self, msg, *args, **kwargs):
        if self.isEnabledFor(NOTICE):
            self._log(NOTICE, msg, args, **kwargs)


def setup_logging(config: Config):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # log file
    file_handler = logging.FileHandler(config.filename)
    file_handler.setFormatter(formatter)

    # notifier
    tg_handler = NotificationHandler(
        "telegram",
        defaults={
            "token": config.telegram.token,
            "chat_id": config.telegram.chat_id,
        },
    )
    tg_handler.setFormatter(formatter)
    tg_handler.setLevel(logging.WARNING)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(tg_handler)

    # setup logger class
    logging.setLoggerClass(MyLogger)


def getLogger(name: str) -> MyLogger:
    logger = logging.getLogger(name)
    return logger  # type: ignore
