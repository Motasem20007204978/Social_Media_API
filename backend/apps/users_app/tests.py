from django.test import TestCase
import requests

# from django.core.files.images import ImageFile
# Create your tests here.

sq = lambda x: x**2
ml = lambda x, y: x * y

# cosine
d1 = [1, 2, 0, -1]
d2 = [2, 0, -1, 0]
d1s = sum(map(sq, d1))
d2s = sum(map(sq, d2))

d = sum(map(ml, d1, d2))

cos = d / (d1s**0.5 * d2s**0.5)
print(cos)


# correlation
d1_mean = sum(d1) / len(d1)
d2_mean = sum(d2) / len(d2)

sub_d1 = [i - d1_mean for i in d1]
sub_d2 = [i - d2_mean for i in d2]

cov = sum(map(ml, sub_d1, sub_d2)) / (len(d1) - 1)

std_d1 = (sum(map(sq, sub_d1)) / (len(d1) - 1)) ** 0.5
std_d2 = (sum(map(sq, sub_d2)) / (len(d2) - 1)) ** 0.5

corr = cov / (std_d1 * std_d2)
print(corr)
