from cgitb import text
from rest_framework.test import APITestCase, URLPatternsTestCase
import base64
from django.urls import path, include, reverse
from django.utils.crypto import get_random_string


class UserAuthTest(APITestCase, URLPatternsTestCase):

    urlpatterns = [path("users/", include("users_app.urls"))]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.password = get_random_string(10)

    def test_create_account(self):
        url = reverse(viewname="user-list-create")
        data = {
            "username": "user_name",
            "email": "user@gmail.com",
            "first_name": "first_name",
            "last_name": "last_name",
            "password": self.password,
            "again_pass": self.password,
        }
        response = self.client.post(path=url, data=data)
        self.assertEqual(response.status_code, 200)
        response_data = {
            "message": "user registerd successfully, we sent emial verification link in your inbox"
        }
        self.assertEqual(response.data, response_data)

    def login_test(self):
        cred = {"email": "user@gmail.com", "password": self.password}
        can_login = self.client.login(credentials=cred)
        self.assertTrue(can_login)

        url = reverse("signin-user")
        response = self.client.post(path=url, data=cred)
        self.assertEquals(response.status_code, 200)
