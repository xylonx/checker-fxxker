import json
import logging
import time
from dataclasses import dataclass
from hashlib import sha256

import requests
from dateutil import parser

HOST = "https://www.universal-cdn.com"


@dataclass
class Config:
    email: str
    password: str


def getSHA256(to_hash: str):
    """Get SHA256 hash."""
    m = sha256()
    m.update(to_hash.encode())
    return m.hexdigest()


def getXHeaders():
    """
    These Xheaders were mainly used to authenticate whether the requests were coming from the actual hanime app and not a script like this one.
    The authentication wasn't that secure tho and reverse engineering it wasn't that difficult.
    """
    XClaim = str(int(time.time()))
    XSig = getSHA256(f"9944822{XClaim}8{XClaim}113")
    headers = {
        "X-Signature-Version": "app2",
        "X-Claim": XClaim,
        "X-Signature": XSig,
    }
    return headers


def getInfo(response: str):
    """Parse out only relevant info."""
    received = json.loads(response)

    ret = {
        "session_token": received["session_token"],
        "uid": received["user"]["id"],
        "name": received["user"]["name"],
        "coins": received["user"]["coins"],
        "last_clicked": received["user"]["last_rewarded_ad_clicked_at"],
    }

    available_keys = list(received["env"]["mobile_apps"].keys())

    if "_build_number" in available_keys:
        ret["version"] = received["env"]["mobile_apps"]["_build_number"]
    elif "osts_build_number" in available_keys:
        ret["version"] = received["env"]["mobile_apps"]["osts_build_number"]
    elif "severilous_build_number" in available_keys:
        ret["version"] = received["env"]["mobile_apps"]["severilous_build_number"]
    else:
        raise Exception(
            "Unable to find the build number for the latest mobile app, please report an issue on github."
        )

    return ret


def login(s: requests.Session, email, password):
    """Login into your hanime account."""
    s.headers.update(getXHeaders())
    response = s.post(
        f"{HOST}/rapi/v4/sessions",
        headers={"Content-Type": "application/json;charset=utf-8"},
        data=f'{{"burger":"{email}","fries":"{password}"}}',
    )

    if '{"errors":["Unauthorized"]}' in response.text:
        raise Exception("Login failed, please check your credentials.")

    return getInfo(response.text)


def getCoins(s: requests.Session, logger: logging.Logger, version, uid):
    """
    Send a request to claim your coins, this request is forged and we are not actually clicking the ad.
    Again, reverse engineering the mechanism of generating the reward token wasn't much obfuscated.
    """
    s.headers.update(getXHeaders())

    curr_time = str(int(time.time()))
    to_hash = f"coins{version}|{uid}|{curr_time}|coins{version}"

    data = {
        "reward_token": getSHA256(to_hash) + f"|{curr_time}",
        "version": f"{version}",
    }

    response = s.post(f"{HOST}/rapi/v4/coins", data=data)

    if '{"errors":["Unauthorized"]}' in response.text:
        raise Exception("Something went wrong, please report issue on github")
    logger.info(f"You received {json.loads(response.text)['rewarded_amount']} coins.")


def checkin(config: Config):
    logger = logging.getLogger(f"[Hanime][{config.email}]")

    try:
        s = requests.Session()
        info = login(s, config.email, config.password)
        logger.info(f"Logged in as {info['name']}")
        logger.info(f"Coins count: {info['coins']}")

        if info["last_clicked"] is not None:
            logger.info(
                f"Last clicked on {parser.parse(info['last_clicked']).ctime()} UTC"
            )

            previous_time = parser.parse(info["last_clicked"]).timestamp()
            if time.time() - previous_time < 3 * 3600:
                raise Exception("You've already clicked on an ad less than 3 hrs ago.")
        else:
            logger.info("Never clicked on an ad")

        getCoins(s, logger, info["version"], info["uid"])
    except BaseException as e:
        logger.error(f"Checkin failed. {e}")
