import requests
import requests.cookies


def session_from_cookie_str(cookie: str) -> requests.Session:
    cookie_dict = {c.split("=")[0]: c.split("=")[1] for c in cookie.split("; ")}

    s = requests.Session()
    s.cookies = requests.cookies.cookiejar_from_dict(cookie_dict)
    return s
