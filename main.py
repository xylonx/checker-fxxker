import argparse
import logging
import time

import schedule

from src.config import parse_config
from src.sites import hanime, p1a3, soushuba, southplus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    filename="app.log",
)


def main(config_file: str):
    with open(config_file) as f:
        config = parse_config(f.read())

        p1a3.checkin(config.p1a3)

        # Hanime
        schedule.every(6).hours.do(hanime.checkin, config=config.hanime)
        # soushuba
        schedule.every().day.do(soushuba.checkin, config=config.soushu)
        # south-plus
        schedule.every().day.do(southplus.daily_checkin, config.southplus)
        schedule.every().week.do(southplus.weekly_checkin, config.southplus)
        # 1p3a
        schedule.every().day.do(p1a3.checkin, config.p1a3)

        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("checkin-fxxker")
    parser.add_argument("config", help="Config file")
    args = parser.parse_args()
    main(args.config)
