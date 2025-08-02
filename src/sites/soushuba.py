import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup
from urllib3.util import Url, parse_url


@dataclass
class Config:
    permenant_url: str
    username: str
    password: str


REDIRECT_RE = re.compile(r'url=(.+)">')


def get_redirect_url(index_url: str) -> str:
    response = requests.get(index_url, verify=False)
    if response.status_code != 403:
        response.raise_for_status()
    if find := REDIRECT_RE.findall(response.text):
        return find[0]
    raise Exception("Failed to find redirect url")


def get_url(url: str) -> str:
    resp = requests.get(url, verify=False)
    soup = BeautifulSoup(resp.content, "html.parser")
    if (tag := soup.find("a", href=True, string="搜书吧")) and tag.has_attr("href"):  # type: ignore
        return tag["href"]  # type: ignore
    raise Exception("Failed to find the latest url")


def get_actual_url(index_url: str) -> str:
    if redirect1 := get_redirect_url(index_url):
        if redirect2 := get_redirect_url(redirect1):
            return get_url(redirect2)
    raise Exception("Failed to retrieve the actual url")


LOGIN_HASH_RE = re.compile(r'<div id="main_messaqge_(.+?)">')
FORM_HASH_RE = re.compile(r'<input type="hidden" name="formhash" value="(.+?)" />')


def login_form_hash(s: requests.Session, url: Url) -> Tuple[str, str]:
    resp = s.get(
        f"https://{url.hostname}/member.php?mod=logging&action=login", verify=False
    ).text
    if (login_hash := LOGIN_HASH_RE.findall(resp)) and (
        form_hash := FORM_HASH_RE.findall(resp)
    ):
        return login_hash[0], form_hash[0]
    raise Exception("Failed to retrive login hash and form hash")


def common_header(url: Url):
    return {
        "Host": f"{url.hostname}",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,cn;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": f"https://{url.hostname}",
    }


def login(
    s: requests.Session,
    logger: logging.Logger,
    url: Url,
    username: str,
    password: str,
    question_id: str = "0",
    answer: Optional[str] = None,
):
    loginhash, formhash = login_form_hash(s, url)
    login_url = f"https://{url.hostname}/member.php?mod=logging&action=login&loginsubmit=yes&handlekey=register&loginhash={loginhash}&inajax=1"

    headers = common_header(url)
    headers["Referer"] = f"https://{url.hostname}/"

    payload = {
        "formhash": formhash,
        "referer": f"https://{url.hostname}/",
        "username": username,
        "password": password,
        "questionid": question_id,
        "answer": answer,
    }

    resp = s.post(login_url, data=payload, headers=headers, verify=False)
    if resp.status_code == 200:
        logger.info(f"Welcome {username}!")
    else:
        raise ValueError("Verify Failed! Check your username and password!")


SPACE_FORM_HASH_RE = re.compile(
    r'<input type="hidden" name="formhash" value="(.+?)" />'
)


def space_form_hash(s: requests.Session, url: Url) -> str:
    user_info_resp = s.get(
        f"https://{url.hostname}/home.php?mod=spacecp&ac=credit&showcredit=1",
        verify=False,
    ).text
    if form_hash := SPACE_FORM_HASH_RE.findall(user_info_resp):
        return form_hash[0]
    raise ValueError("Failed to find space form hash")


def space(s: requests.Session, logger: logging.Logger, url: Url):
    form_hash = space_form_hash(s, url)

    headers = common_header(url)
    headers["Referer"] = f"https://{url.hostname}/home.php"

    for x in range(5):
        payload = {
            "message": "开心赚银币 {0} 次".format(x + 1).encode("GBK"),
            "addsubmit": "true",
            "spacenote": "true",
            "referer": "home.php",
            "formhash": form_hash,
        }
        resp = s.post(
            f"https://{url.hostname}/home.php?mod=spacecp&ac=doing&handlekey=doing&inajax=1",
            data=payload,
            headers=headers,
            verify=False,
        )
        if re.search("操作成功", resp.text):
            logger.info(f"Post {x + 1}nd successfully!")
            time.sleep(120)
        else:
            logger.warning(f"Post {x + 1}nd failed!")


def credit(s: requests.Session, url: Url) -> str:
    credit_resp = s.get(
        f"https://{url.hostname}/home.php?mod=spacecp&ac=credit&showcredit=1&inajax=1&ajaxtarget=extcreditmenu_menu",
        verify=False,
    ).text

    # 解析 XML，提取 CDATA
    root = ET.fromstring(str(credit_resp))
    # cdata_content = root.text
    if cdata_content := root.text:
        # 使用 BeautifulSoup 解析 CDATA 内容
        cdata_soup = BeautifulSoup(cdata_content, features="lxml")
        if (hcredit_2 := cdata_soup.find("span", id="hcredit_2")) and (
            credit := hcredit_2.string  # type: ignore
        ):
            return credit
    raise ValueError("Failed to retrieve the credit")


def checkin(config: Config):
    logger = logging.getLogger(f"[搜书吧][{config.username}]")

    try:
        s = requests.Session()
        actual_url = get_actual_url(config.permenant_url)
        actual_url = parse_url(actual_url)
        login(s, logger, actual_url, config.username, config.password)
        space(s, logger, actual_url)
        cred = credit(s, actual_url)
        logger.info(f"{config.username} have {cred} coins!")
    except BaseException as e:
        logger.error(f"Failed to checkin: {e}")
