from django.test import TestCase
import base64

with open("C://Users/motasem/Desktop/20220309_143200.jpg", "rb") as image:
    enc = base64.b85encode(image.read())

print(enc.decode("utf-8"))

"""
 
"""
