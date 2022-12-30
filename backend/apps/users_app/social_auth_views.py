import email
import re
from rest_framework.views import APIView
from django.shortcuts import redirect
from rest_framework.response import Response
import requests
from rest_framework.permissions import AllowAny
from django.conf import settings
from io import BytesIO
from PIL import Image
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

# Set the API endpoint and your app's consumer key and secret
TWITTER_API_ENDPOINT = "https://api.twitter.com"
TWITTER_CLIENT_KEY = settings.TWITTER_CLIENT_KEY
TWITTER_CLIENT_SECRET = settings.TWITTER_CLIENT_SECRET
TWITTER_CALLBACK_URI = settings.TWITTER_CALLBACK_URI


class LoginTwitterView(APIView):
    permission_classes = [AllowAny]

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


class LoginTwitterCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Get the request token and verifier from the query string
        request_token = request.GET.get("oauth_token")
        verifier = request.GET.get("oauth_verifier")

        request_url = f"{TWITTER_API_ENDPOINT}/oauth/request_token"
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"}

        # Set the request payload and send the request to get the request token
        payload = {
            "oauth_token": request_token,
            "oauth_verifier": verifier,
        }
        # Send the request to get the access token
        response = requests.post(
            request_url,
            headers=headers,
            auth=(TWITTER_CLIENT_KEY, TWITTER_CLIENT_SECRET),
            data=payload,
        )

        # Get the access token from the response
        access_token = response.text.split("&")[0].split("=")[1]
        access_token_secret = response.text.split("&")[1].split("=")[1]

        # Set the request URL and headers for the user data request
        request_url = f"{TWITTER_API_ENDPOINT}/1.1/account/verify_credentials.json"
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        # Send the request to get the user data
        response = requests.get(
            request_url,
            headers=headers,
            auth=(TWITTER_CLIENT_KEY, TWITTER_CLIENT_SECRET),
        )

        # Get the user data from the response
        user_data = response.json()

        return Response(data=user_data)


GOOGLE_CLIENT_KEY = settings.GOOGLE_CLIENT_KEY
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_CALLBACK_URI = settings.GOOGLE_CALLBACK_URI


class LoginGoogleAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):

        # Redirect the user to the Google OAuth 2.0 authorization endpoint
        return redirect(
            f"https://accounts.google.com/o/oauth2/v2/auth?client_id={GOOGLE_CLIENT_KEY}&redirect_uri={GOOGLE_CALLBACK_URI}&response_type=code&scope=email%20profile"
        )


class LoginGoogleCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Get the authorization code from the query string
        code = request.GET.get("code")

        # Set the request URL and headers for the access token request
        request_url = "https://oauth2.googleapis.com/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Set the request payload
        payload = {
            "code": code,
            "client_id": GOOGLE_CLIENT_KEY,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_CALLBACK_URI,
            "grant_type": "authorization_code",
        }

        # Send the request to exchange the authorization code for an access token
        response = requests.post(request_url, headers=headers, data=payload)

        # Get the access token from the response
        access_token = response.json()["access_token"]

        # Set the request URL and headers for the user data request
        request_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        # Send the request to get the user data
        response = requests.get(request_url, headers=headers)

        # Get the user data from the response
        user_data = response.json()

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
        if not User.objects.filter(email=data["email"]):
            User.objects.create_social_user(**data)

        login_data = {
            "email": data["email"],
            "password": settings.LOGIN_WITH_SOCIAL_MEDIA_PASS,
        }
        url = request.build_absolute_uri(reverse("signin-user"))
        print(url)
        req = requests.post(url=url, data=login_data)
        return Response(data=req.json())
