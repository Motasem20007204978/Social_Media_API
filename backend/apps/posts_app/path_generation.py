from django.utils.deconstruct import deconstructible
from uuid import uuid4
import os

@deconstructible
class PathAndRename(object):
    def __init__(self, sub_path):
        self.path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split(".")[-1]
        filename = "{}.{}".format(uuid4().hex, ext)
        print(self.path)
        return os.path.join(self.path, filename)