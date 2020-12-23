from django.urls import path

from cart import views

urlpatterns = [
    path("option/", views.CartViewSet.as_view({"post": "add_cart",
                                               "get": "list_cart",
                                               "patch": "change_status",
                                               'delete': "delete_course",
                                               "put": "change_expire"})),
    path("order/", views.CartViewSet.as_view({"get": "get_select_course"})),
]
