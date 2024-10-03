from rest_framework.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    """Пагинация для рецептов и пользователей."""
    page_size_query_param = 'limit'
    page_size = 6
