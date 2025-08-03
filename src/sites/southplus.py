import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from src.utils import logging
from src.utils.cookie import session_from_cookie_str

dailyLogger = logging.getLogger("[SouthPlus][日常]")
weeklyLogger = logging.getLogger("[SouthPlus][周常]")


@dataclass
class Config:
    cookie: str


def common_header():
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en-GB;q=0.8,en-US;q=0.7,en;q=0.6,zh-TW;q=0.5",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    }


VERIFY_HASH_RE = re.compile(r"var verifyhash = '([A-Za-z0-9]+)';")


def get_verify_hash(s: requests.Session) -> str:
    headers = common_header()
    headers["sec-fetch-dest"] = "document"
    headers["sec-fetch-mode"] = "navigate"
    headers["sec-fetch-site"] = "none"
    headers["sec-fetch-user"] = "?1"

    resp = s.get(
        "https://www.south-plus.net/plugin.php?H_name-tasks.html",
        headers=headers,
    ).text
    if found := VERIFY_HASH_RE.findall(resp):
        return found[0]
    raise ValueError("Failed to find verify hash")


def get_sp(s: requests.Session) -> str:
    headers = common_header()

    resp = s.get("https://www.south-plus.net/index.php", headers=headers).text
    soup = BeautifulSoup(resp, "html.parser")
    if sp_coin_span := soup.find("span", class_="s3 f10"):
        return sp_coin_span.text
    raise ValueError("Failed to collect SP")


# Daily
def daily_apply(s: requests.Session, verify: str):
    headers = common_header()
    headers["referrer"] = "https://www.south-plus.net/plugin.php?H_name-tasks.html"
    headers["sec-fetch-dest"] = "iframe"
    headers["sec-fetch-mode"] = "navigate"
    headers["sec-fetch-site"] = "same-origin"
    headers["sec-fetch-user"] = "?1"

    params = {
        "H_name": "tasks",
        "action": "ajax",
        "actions": "job",
        "cid": "15",
        "nowtime": f"{int(time.time() * 1000)}",
        "verify": verify,
    }

    response = s.get(
        "https://www.south-plus.net/plugin.php",
        params=params,
        headers=headers,
    ).text

    root = ET.fromstring(response)
    if cdata := root.text:
        dailyLogger.notice(f"{cdata}")
    else:
        raise ValueError("Failed to apply daily task")


def daily_collect(s: requests.Session, verify: str):
    headers = common_header()
    headers["sec-fetch-dest"] = "iframe"
    headers["sec-fetch-mode"] = "navigate"
    headers["sec-fetch-site"] = "same-origin"
    headers["sec-fetch-user"] = "?1"

    params = {
        "H_name": "tasks",
        "action": "ajax",
        "actions": "job2",
        "cid": "15",
        "nowtime": f"{int(time.time() * 1000)}",
        "verify": verify,
    }

    response = s.get(
        "https://www.south-plus.net/plugin.php",
        params=params,
        headers=headers,
    ).text

    root = ET.fromstring(response)
    if cdata := root.text:
        dailyLogger.notice(f"{cdata}")
    else:
        raise ValueError("Failed to collect daily task")


def daily_checkin(config: Config):
    try:
        s = session_from_cookie_str(config.cookie)
        verify = get_verify_hash(s)
        daily_apply(s, verify)
        daily_collect(s, verify)
        sp = get_sp(s)
        dailyLogger.notice(f"Current SP: {sp}")
    except BaseException as err:
        dailyLogger.error(f"Failed to checkin: {err}")


# Weekly


def weekly_apply(s: requests.Session, verify: str):
    headers = common_header()
    headers["referrer"] = "https://www.south-plus.net/plugin.php?H_name-tasks.html"
    headers["sec-fetch-dest"] = "iframe"
    headers["sec-fetch-mode"] = "navigate"
    headers["sec-fetch-site"] = "same-origin"
    headers["sec-fetch-user"] = "?1"

    params = {
        "H_name": "tasks",
        "action": "ajax",
        "actions": "job",
        "cid": "14",
        "nowtime": f"{int(time.time() * 1000)}",
        "verify": verify,
    }

    response = s.get(
        "https://www.south-plus.net/plugin.php",
        params=params,
        headers=headers,
    ).text

    root = ET.fromstring(response)
    if cdata := root.text:
        weeklyLogger.notice(f"{cdata}")
    else:
        raise ValueError("Failed to apply daily task")


def weekly_collect(s: requests.Session, verify: str):
    headers = common_header()
    headers["sec-fetch-dest"] = "iframe"
    headers["sec-fetch-mode"] = "navigate"
    headers["sec-fetch-site"] = "same-origin"
    headers["sec-fetch-user"] = "?1"

    params = {
        "H_name": "tasks",
        "action": "ajax",
        "actions": "job2",
        "cid": "14",
        "nowtime": f"{int(time.time() * 1000)}",
        "verify": verify,
    }

    response = s.get(
        "https://www.south-plus.net/plugin.php",
        params=params,
        headers=headers,
    )

    root = ET.fromstring(response.text)
    if cdata := root.text:
        weeklyLogger.notice(f"{cdata}")
    else:
        raise ValueError("Failed to collect daily task")


def weekly_checkin(config: Config):
    try:
        s = session_from_cookie_str(config.cookie)
        verify = get_verify_hash(s)
        weekly_apply(s, verify)
        weekly_collect(s, verify)
        sp = get_sp(s)
        weeklyLogger.notice(f"Current SP: {sp}")
    except BaseException as err:
        weeklyLogger.error(f"Failed to checkin: {err}")
