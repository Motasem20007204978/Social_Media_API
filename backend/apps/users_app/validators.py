import requests
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from decouple import config
from django.core.exceptions import ValidationError


class UserNameValidator(RegexValidator):
    regex = r"^[A-Za-z][\w.]{7,}$"
    message = _(
        "enter username with A-Z, a-z asscii characters, 0-9, or _"
        " between 8 and 30 characters, must begins with letter"
    )
    flags = 0


username_validator = UserNameValidator()


class NameValidator(RegexValidator):
    regex = r"^[A-Za-z]{5,}"
    message = _("enter name with A-Z or a-z" " between 8 and 30 characters")
    flags = 0


name_validator = NameValidator()


async def is_real_email(email: str):
    api_key = config("CHECK_EMAIL_API_KEY")
    email_address = email
    response = requests.get(
        "https://isitarealemail.com/api/email/validate",
        params={"email": email_address},
        headers={"Authorization": "Bearer " + api_key},
    )

    status = response.json()["status"]
    if status != "valid":
        raise ValidationError("email is not real email")
