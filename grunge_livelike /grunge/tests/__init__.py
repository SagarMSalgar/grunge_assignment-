from django.conf import settings
from rest_framework.test import APITestCase


class BaseAPITestCase(APITestCase):
    fixtures = ["initial_data"]
    version = settings.REST_FRAMEWORK["DEFAULT_VERSION"]
