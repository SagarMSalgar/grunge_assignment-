from django.conf import settings
from rest_framework.pagination import PageNumberPagination as DRFPageNumberPagination


class PageNumberPagination(DRFPageNumberPagination):

    page_size_query_param = settings.PAGE_SIZE_QUERY_PARAM
