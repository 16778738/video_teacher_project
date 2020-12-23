from django.urls import path

from home import views

urlpatterns = [
    path("banner/", views.BannerListAPIView.as_view()),
    path("nav/", views.NavListAPIView.as_view()),
]
