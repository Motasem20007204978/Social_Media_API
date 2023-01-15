import re
from io import BytesIO

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from PIL import Image
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

User = get_user_model()

# Set the API endpoint and your app's consumer key and secret
TWITTER_API_ENDPOINT = "https://api.twitter.com"
TWITTER_CLIENT_KEY = settings.TWITTER_CLIENT_KEY
TWITTER_CLIENT_SECRET = settings.TWITTER_CLIENT_SECRET
TWITTER_CALLBACK_URI = settings.TWITTER_CALLBACK_URI


class GenericLoginView(GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):

        access_token = self.get_access_token(kwargs.get("auth_data"))

        user_data = self.get_user_data(access_token=access_token)

        # create user if it is not exist
        user = self.perform_creation(user_data)

        login_data = {
            "email": user.email,
            "password": settings.LOGIN_WITH_SOCIAL_MEDIA_PASS,
        }
        login_response = self.perform_login(login_data)
        return Response(data=login_response.json())


class CallBackView(GenericLoginView):
    def get_access_token(self, **kwargs):
        # Send the request to get the access token
        response = requests.post(
            url=kwargs.get("url"),
            headers=kwargs.get("headers"),
            auth=kwargs.get("auth"),
            data=kwargs.get("payload"),
        )
        return response

    def get_user_data(self, **kwargs):
        response = requests.get(
            kwargs.get("url"), headers=kwargs.get("headers"), auth=kwargs.get("auth")
        )
        return response.json()

    def perform_creation(self, user_data):
        user = User.objects.create_social_user(**user_data)
        return user

    def perform_login(self, credentials):
        url = self.request.build_absolute_uri(reverse("signin-user"))
        response = requests.post(url=url, data=credentials)
        return response


class LoginTwitterView(GenericLoginView):
    def get(self, request, *args, **kwargs):

        # Set the callback URL and request URL
        request_url = f"{TWITTER_API_ENDPOINT}/oauth/request_token"

        # Set the request headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }

        # Set the request payload
        payload = {
            "oauth_callback": TWITTER_CALLBACK_URI,
        }

        # Send the request to get the request token
        response = requests.post(
            request_url,
            headers=headers,
            auth=(TWITTER_CLIENT_KEY, TWITTER_CLIENT_SECRET),
            data=payload,
        )

        # Get the request token from the response
        request_token = response.text.split("&")[0].split("=")[1]

        # Redirect the user to the Twitter login page
        return redirect(
            f"{TWITTER_API_ENDPOINT}/oauth/authenticate?oauth_token={request_token}"
        )


class LoginTwitterCallbackView(CallBackView):
    def get_access_token(self, kwargs):
        oauth_token = kwargs.get("oauth_token")
        oauth_verifier = kwargs.get("oauth_verifier")

        request_url = f"{TWITTER_API_ENDPOINT}/oauth/request_token"
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}

        # Set the request payload and send the request to get the request token
        payload = {
            "oauth_token": oauth_token,
            "oauth_verifier": oauth_verifier,
        }
        # Send the request to get the access token
        response = super().get_access_token(
            url=request_url,
            headers=headers,
            auth=(TWITTER_CLIENT_KEY, TWITTER_CLIENT_SECRET),
            payload=payload,
        )

        # Get the access token from the response
        access_token = response.text.split("&")[0].split("=")[1]
        return access_token

    def get_user_data(self, **kwargs):
        # Set the request URL and headers for the user data request
        request_url = f"{TWITTER_API_ENDPOINT}/1.1/account/verify_credentials.json"
        headers = {
            "Authorization": f"Bearer {kwargs.get('access_token')}",
        }

        # Send the request to get the user data
        json_data = super().get_user_data(
            url=request_url,
            headers=headers,
            auth=(TWITTER_CLIENT_KEY, TWITTER_CLIENT_SECRET),
        )

        return json_data

    def get(self, request, *args, **kwargs):
        # Get the request token and verifier from the query string
        auth_data = {
            "request_token": request.GET.get("oauth_token"),
            "oauth_verifier": request.GET.get("oauth_verifier"),
        }

        kwargs["auth_data"] = auth_data
        return super().get(request, *args, **kwargs)


GOOGLE_CLIENT_KEY = settings.GOOGLE_CLIENT_KEY
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_CALLBACK_URI = settings.GOOGLE_CALLBACK_URI


class LoginGoogleAPIView(GenericLoginView):
    def get(self, request, *args, **kwargs):

        # Redirect the user to the Google OAuth 2.0 authorization endpoint
        return redirect(
            f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_KEY}&redirect_uri={GOOGLE_CALLBACK_URI}&response_type=code&scope=email%20profile"
        )


class LoginGoogleCallbackAPIView(CallBackView):
    def get_access_token(self, auth_data):

        # Set the request URL and headers for the access token request
        request_url = "https://oauth2.googleapis.com/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Set the request payload
        payload = {
            "code": auth_data.get("code"),
            "client_id": GOOGLE_CLIENT_KEY,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_CALLBACK_URI,
            "grant_type": "authorization_code",
        }
        # Send the request to exchange the authorization code for an access token
        response = super().get_access_token(
            url=request_url, headers=headers, payload=payload
        )

        # Get the access token from the response
        access_token = response.json()["access_token"]
        return access_token

    def get_user_data(self, **kwargs):

        # Set the request URL and headers for the user data request
        request_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {
            "Authorization": f"Bearer {kwargs.get('access_token')}",
        }
        # Send the request to get the user data
        json_data = super().get_user_data(url=request_url, headers=headers)
        return json_data

    def perform_creation(self, user_data):

        user = User.objects.filter(email=user_data["email"])
        if user.exists():
            return user[0]

        picture = requests.get(user_data.get("picture"))
        profile_pic = Image.open(BytesIO(picture.content))
        username = re.sub(r"[^a-zA-Z]", "_", user_data.get("name"))
        data = {
            "provider": "google",
            "username": username,
            "email": user_data.get("email"),
            "first_name": user_data.get("given_name"),
            "last_name": user_data.get("family_name"),
            # "profile_pic": profile_pic,
            "password": settings.LOGIN_WITH_SOCIAL_MEDIA_PASS,
        }
        return super().perform_creation(data)

    def get(self, request, *args, **kwargs):

        # Get the authorization code from the query string
        auth_data = {"code": request.GET.get("code")}
        kwargs["auth_data"] = auth_data
        return super().get(request, *args, **kwargs)
