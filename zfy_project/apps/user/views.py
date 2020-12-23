import random
import re

from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.views import APIView

from user.models import UserInfo
from user.serrializer import UserModelSerializer
from user.utils import get_user_by_account
from zfy_project.libs.geetest import GeetestLib
from zfy_project.utils import contastnt
from zfy_project.utils.random_code import create_random_code
from zfy_project.utils.send_msg import Message

pc_geetest_id = "1ea3ed8b35299a931b6a3883ec4a05be"
pc_geetest_key = "9a13879615c1ae2500e356417cd5bcf9"


class CaptchaAPIView(APIView):
    '''
    滑块验证码
    '''
    user_id = 0
    status = False

    # pc端获取验证码的方法
    def get(self, request, *args, **kwargs):
        username = request.query_params.get("username")
        user = get_user_by_account(username)
        if user is None:
            return Response({"message": "用户存在"}, status=http_status.HTTP_400_BAD_REQUEST)
        self.user_id = user.id
        # 验证码的实例化对象
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        self.status = gt.pre_process(self.user_id)
        response_str = gt.get_response_str()
        return Response(response_str)

    # pc端基于前后端分离校验验证码
    def post(self, request, *args, **kwargs):
        """验证验证码"""
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        if self.user_id:
            result = gt.success_validate(challenge, validate, seccode, self.user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        result = {"status": "success"} if result else {"status": "fail"}
        return Response(result)


class UserAPIView(CreateAPIView):
    '''用户注册'''
    queryset = UserInfo.objects.all()
    serializer_class = UserModelSerializer


class MobileCheckAPIView(APIView):
    def get(self, request):
        phone = request.query_params.get("phone")
        # 验证手机号格式
        if not re.match(r'^1[34578]\d{9}$', phone):
            return Response({
                "message": "手机号格式不正确"
            }, status=http_status.HTTP_400_BAD_REQUEST)
        # 判断是否手机号已被注册
        user = get_user_by_account(phone)
        if user is not None:
            return Response({
                "message": "手机号已被注册"
            }, status=http_status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "ok"
        })


class PasswdCheckAPIView(APIView):
    '''密码校验'''

    def post(self, request, *args, **kwargs):
        password = request.data['password']
        print(password)
        if re.match(r'^.*(?=.{6,})(?=.*\d)(?=.*[A-Za-z])(?=.*[!@#$%^&*?]).*$', password):
            return Response({
                "message": "密码是高级密码",
            }, status=http_status.HTTP_200_OK)
        elif re.match(r'^.*(?=.{6,})(?=.*\d)(?=.*[A-Za-z]).*$', password):
            return Response({
                "message": "密码是中级密码",
            }, status=http_status.HTTP_200_OK)
        elif re.match(r'^.*(?=.{6,})(?=.*\d).*$|^.*(?=.{6,})(?=.*[A-Za-z]).*$', password):
            return Response({
                "message": "密码为弱密码",
            }, status=http_status.HTTP_200_OK)
        else:
            return Response({
                "message": "密码不符合规范",
            }, status=http_status.HTTP_400_BAD_REQUEST)


class SendMessageAPIView(APIView):
    """短信注册业务"""

    def get(self, request, *args, **kwargs):
        """
        获取验证码   为手机号生成验证码并发送
        :param request:
        :return:
        """
        phone = request.query_params.get("phone")

        # 获取redis连接
        redis_connection = get_redis_connection("sms_code")

        # TODO 1.判断用户60s内是否发送过验证码
        mobile_code = redis_connection.get("sms_%s" % phone)

        if mobile_code is not None:
            return Response({"message": "您已经在60s内发送过短信了，请稍等~"},
                            status=http_status.HTTP_400_BAD_REQUEST)

        # TODO 2.生成随机验证码
        code = "%06d" % random.randint(0, 999999)
        print(code)

        # TODO 3.将验证码保存在redis中
        redis_connection.setex("sms_%s" % phone, contastnt.SMS_EXPIRE_TIME, code)  # 验证码间隔时间
        redis_connection.setex("mobile_%s" % phone, contastnt.CODE_EXPIRE_TIME, code)  # 验证码有效期

        # TODO 4.完成短信的发送
        try:
            message = Message(contastnt.API_KEY)
            message.send_message(phone, code)
        except:
            return Response({"message": "验证码发送失败"},
                            status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

        # TODO 5.将发送的结果响应回去
        return Response({"message": "短信发送成功"},
                        status=http_status.HTTP_200_OK)


class Mobile1CheckAPIView(APIView):
    '''短信登陆判断电话是否注册'''

    def get(self, request):
        phone = request.query_params.get("phone")
        print(phone)
        # 验证手机号格式
        if not re.match(r'^1[34578]\d{9}$', phone):
            return Response({
                "message": "手机号格式不正确"
            }, status=http_status.HTTP_400_BAD_REQUEST)
        # 判断是否手机号已被注册
        user = get_user_by_account(phone)
        if user is not None:
            return Response({
                "message": "手机号已被注册"
            }, status=http_status.HTTP_200_OK)
        return Response({
            "message": "手机号没有注册"
        }, status=http_status.HTTP_400_BAD_REQUEST)


class PhoneUserAPIView(APIView):
    '''短信登陆业务'''

    # TODO  获取前端传递的手机号,验证码
    def get(self, request):
        phone = request.query_params.get("phone")
        code = request.query_params.get("code")
        print(code)

        # TODO 校验验证码是否一致
        redis_connection = get_redis_connection("sms_code")
        mobile_code = redis_connection.get("mobile_%s" % phone)
        # redis数据库中存储的数据为二进制 需要decode编码
        if mobile_code.decode() != code:
            # 代表验证码有误
            # 为了防止暴力破解  可以设置一个手机号只能验证n次  累加
            return Response({
                "message": "验证码不一致"
            }, status=http_status.HTTP_400_BAD_REQUEST)
        # 验证通过后将redis的验证码的删除
        return Response({
            'message': "登陆成功"
        }, status=http_status.HTTP_200_OK)
