from dataclasses import dataclass

import mashumaro.codecs.yaml as yaml_codec

from src.sites import hanime, p1a3, soushuba, southplus


@dataclass
class ApplicationConfig:
    db_uri: str
    log_file: str


@dataclass
class TelegramNotificationConfig:
    token: str
    chat_id: str


@dataclass
class NotificationConfig:
    telegram: TelegramNotificationConfig


@dataclass
class Config:
    application: ApplicationConfig
    notification: NotificationConfig
    hanime: hanime.Config
    soushu: soushuba.Config
    southplus: southplus.Config
    p1a3: p1a3.Config


def parse_config(data: str) -> Config:
    return yaml_codec.decode(data, Config)
