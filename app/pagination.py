from rest_framework.pagination import PageNumberPagination

class RADefaultPagination(PageNumberPagination):
    page_size = 25                       # Valor por defecto si no envías page_size
    page_query_param = "page"            # React-Admin ya envía page=1,2,3...
    page_size_query_param = "page_size"  # <-- Esto habilita ?page_size=
    max_page_size = 1000