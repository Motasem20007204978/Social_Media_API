from __future__ import print_function
from google_auth_oauthlib.flow import InstalledAppFlow

PATH = __file__.removesuffix("google_auth.py")

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]


def google_login_data():
    """Shows basic usage of the People API.
    Prints the name of the first 10 connections.
    """
    print("hello google")
    flow = InstalledAppFlow.from_client_secrets_file(
        f"{PATH}credentials.json",
        SCOPES,
    )
    flow.run_local_server()

    session = flow.authorized_session()

    profile_info = session.get("https://www.googleapis.com/userinfo/v2/me").json()

    return profile_info
