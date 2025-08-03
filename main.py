import argparse
import logging
import sys

from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from notifiers.logging import NotificationHandler

from src.config import Config, parse_config
from src.sites import hanime, p1a3, soushuba, southplus


def schedule(config: Config):
    jobstores = {
        "default": SQLAlchemyJobStore(url=config.application.db_uri),
    }
    executors = {
        "default": ThreadPoolExecutor(20),
        "processpool": ProcessPoolExecutor(5),
    }
    job_defaults = {
        "coalesce": False,
        "max_instances": 1,
    }
    scheduler = BlockingScheduler(
        jobstores=jobstores, executors=executors, job_defaults=job_defaults
    )

    # Hanime
    scheduler.add_job(
        hanime.checkin,
        kwargs={"config": config.hanime},
        trigger=IntervalTrigger(hours=6),
        id="hanime",
        replace_existing=True,
    )
    # soushuba
    scheduler.add_job(
        soushuba.checkin,
        kwargs={"config": config.soushu},
        trigger=CronTrigger(hour=8),
        id="soushuba",
        replace_existing=True,
    )
    # south-plus
    scheduler.add_job(
        southplus.daily_checkin,
        kwargs={"config": config.southplus},
        trigger=CronTrigger(hour=10, minute=30),
        id="southplus[daily]",
        replace_existing=True,
    )
    scheduler.add_job(
        southplus.weekly_checkin,
        kwargs={"config": config.southplus},
        trigger=CronTrigger(day_of_week="mon", hour=9),
        id="southplus[weekly]",
        replace_existing=True,
    )
    # 1p3a
    scheduler.add_job(
        p1a3.checkin,
        kwargs={"config": config.p1a3},
        trigger=CronTrigger(hour=14, minute=24),
        id="p1a3",
        replace_existing=True,
    )

    return scheduler


def setup_logging(config: Config):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # log file
    file_handler = logging.FileHandler(config.application.log_file)
    file_handler.setFormatter(formatter)

    # notifier
    tg_handler = NotificationHandler(
        "telegram",
        defaults={
            "token": config.notification.telegram.token,
            "chat_id": config.notification.telegram.chat_id,
        },
        raise_on_errors=False,
    )
    tg_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(tg_handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("checkin-fxxker")
    parser.add_argument("config", help="Config file")
    args = parser.parse_args()

    with open(args.config) as f:
        config = parse_config(f.read())

        setup_logging(config)

        scheduler = schedule(config)
        scheduler.start()
