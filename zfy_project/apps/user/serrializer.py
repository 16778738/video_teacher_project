import re

from django.contrib.auth.hashers import make_password
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from django_redis import get_redis_connection

from user.models import UserInfo
from user.utils import get_user_by_account


class UserModelSerializer(ModelSerializer):
    '''
    注册用户时,用户名不能为空
    前端提供的数据必须符合校验规则才可以
    '''
    token = serializers.CharField(max_length=1024, read_only=True, help_text="用户token")
    code = serializers.CharField(write_only=True, help_text="手机验证码")

    class Meta:
        model = UserInfo
        fields = ("phone", "password", "id", "username", "token", "code")
        extra_kwargs = {
            "phone": {
                "write_only": True,
            },
            "password": {
                "write_only": True,
            },
            "username": {
                "read_only": True,
            },
            "id": {
                "read_only": True,
            },
        }

    # 全局钩子 完成用户数据的校验
    def validate(self, attrs):
        phone = attrs.get("phone")
        sms_code = attrs.get("code")  # 手机验证码

        # 验证手机号格式
        if not re.match(r'^1[34578]\d{9}$', phone):
            raise serializers.ValidationError("手机号格式错误")

        # 验证手机号是否被注册
        try:
            user = get_user_by_account(phone)
        except UserInfo.DoesNotExist:
            user = None

        if user:
            raise serializers.ValidationError("当前手机号已经被注册")

        # TODO 校验验证码是否一致
        redis_connection = get_redis_connection("sms_code")
        mobile_code = redis_connection.get("mobile_%s" % phone)
        # redis数据库中存储的数据为二进制 需要decode编码
        if mobile_code.decode() != sms_code:
            # 代表验证码有误
            # 为了防止暴力破解  可以设置一个手机号只能验证n次  累加
            raise serializers.ValidationError("验证码不一致")

        # 验证通过后将redis的验证码的删除

        return attrs

    # TODO 校验密码的格式 局部钩子
    def validate_password(self, attrs):
        password = attrs
        print(password)
        if re.match(r'^.*(?=.{6,})(?=.*\d)(?=.*[A-Za-z])(?=.*[!@#$%^&*?]).*$', password):
            return Response({
                "message": "密码是高级密码",
            },status=status.HTTP_200_OK)
        elif re.match(r'^.*(?=.{6,})(?=.*\d)(?=.*[A-Za-z]).*$', password):
            return Response({
                "message": "密码是中级密码",
            },status=status.HTTP_200_OK)
        elif re.match(r'^.*(?=.{6,})(?=.*\d).*$|^.*(?=.{6,})(?=.*[A-Za-z]).*$', password):
            return Response({
                "message": "密码为弱密码",
            },status=status.HTTP_200_OK)
        else:
            raise serializers.ValidationError("密码输入有误")

    def create(self, validated_data):
        """用户默认信息设置"""
        # 获取密码  对密码进行加密
        password = validated_data.get("password")
        hash_password = make_password(password)

        # 处理用户名的默认值  随机字符串  手机号
        username = validated_data.get("phone")

        # 保存数据
        user = UserInfo.objects.create(
            phone=username,
            username=username,
            password=hash_password
        )

        # 为注册的用户手动生成token
        from rest_framework_jwt.settings import api_settings
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        user.token = jwt_encode_handler(payload)

        return user


