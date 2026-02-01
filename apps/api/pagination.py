from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class that allows clients to override page size.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000
