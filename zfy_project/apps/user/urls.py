from django.urls import path
from rest_framework_jwt.views import obtain_jwt_token

from user import views


urlpatterns = [
    path("login/", obtain_jwt_token),

    path("phone_login/", views.PhoneUserAPIView.as_view()),
    path("phone/", views.MobileCheckAPIView.as_view()),
    path("phone1/", views.Mobile1CheckAPIView.as_view()),
    path("passwd/", views.PasswdCheckAPIView.as_view()),
    path("captcha/", views.CaptchaAPIView.as_view()),
    path("register/", views.UserAPIView.as_view()),
    path("send/", views.SendMessageAPIView.as_view()),

]


