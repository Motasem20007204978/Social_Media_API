from django.test import TestCase

# Create your tests here.
from django.utils.crypto import get_random_string

print(get_random_string(30))
