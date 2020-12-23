import os
from datetime import datetime

from alipay import AliPay
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from course.models import CourseExpire
from order.models import Order
from payments.models import UserCourse


class AliPayAPIView(APIView):

    def get(self, request):
        """获取支付宝的支付链接"""
        order_number = request.query_params.get("order_number")

        # 查询当前订单是否存在
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({"message": "对不起，当前订单不存在"}, status=status.HTTP_400_BAD_REQUEST)

        # 初始化支付宝所需的参数
        alipay = AliPay(
            appid=settings.ALIAPY_CONFIG['appid'],  # 沙箱应用的id
            app_notify_url=settings.ALIAPY_CONFIG['app_notify_url'],  # 默认回调url
            # k开发者私钥
            app_private_key_string=settings.ALIAPY_CONFIG['app_private_key_path'],
            # app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=settings.ALIAPY_CONFIG['alipay_public_key_path'],
            # alipay_public_key_string=alipay_public_key_string,
            sign_type=settings.ALIAPY_CONFIG['sign_type'],  # RSA 或者 RSA2
            debug=settings.ALIAPY_CONFIG['debug'],  # 默认False
        )

        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            # 支付宝所接受的订单号
            out_trade_no=order.order_number,
            # 总价
            total_amount=float(order.real_price),
            subject=order.order_title,
            return_url=settings.ALIAPY_CONFIG['return_url'],
            notify_url=settings.ALIAPY_CONFIG['notify_url'],  # 可选, 不填则使用默认notify url
        )

        # 生成支付链接需要将订单信息与网管拼接起来才可以进行访问
        url = settings.ALIAPY_CONFIG['gateway_url'] + order_string

        return Response(url)


class AliPayResultAPIView(APIView):
    """
    处理支付成功后的业务
    1. 修改订单状态
    2. 生成用户购买记录
    3. 展示结算信息
    """

    def get(self, request):
        # 初始化支付宝所需的参数
        alipay = AliPay(
            appid=settings.ALIAPY_CONFIG['appid'],  # 沙箱应用的id
            app_notify_url=settings.ALIAPY_CONFIG['app_notify_url'],  # 默认回调url
            # k开发者私钥
            app_private_key_string=settings.ALIAPY_CONFIG['app_private_key_path'],
            # app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=settings.ALIAPY_CONFIG['alipay_public_key_path'],
            # alipay_public_key_string=alipay_public_key_string,
            sign_type=settings.ALIAPY_CONFIG['sign_type'],  # RSA 或者 RSA2
            debug=settings.ALIAPY_CONFIG['debug'],  # 默认False
        )

        # 验证支付宝的异步通知，data来自于支付宝回调函数
        data = request.query_params.dict()

        # 获取签名信息
        signature = data.pop("sign")

        # 比对签名是否合法
        success = alipay.verify(data, signature)

        if success:
            # TODO 进行支付成功的业务逻辑
            self.order_result(data)
            return self.order_result(data)

        return Response({"message": "对不起，当前订单支付失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def order_result(self, data):
        """处理支付成功的业务"""

        # 先查询订单是否成功
        order_number = data.get("out_trade_no")
        # print(order_number,'获取返回的订单号')
        # 查询当前订单是否存在
        try:
            order = Order.objects.get(order_number=order_number)
        except Order.DoesNotExist:
            return Response({"message": "对不起，当前订单不存在"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # TODO 1. 修改订单状态
            order.pay_time = datetime.now()
            order.order_status = 1
            order.save()

            # TODO 2. 为用户生成购买记录
            # 用户信息  课程信息  流水号
            user = order.user

            order_detail_list = order.order_courses.all()
            # print(order_detail_list)
            # 获取订单页所展示的信息
            course_list = []

            for course_detail in order_detail_list:
                """遍历此次订单中所有的课程"""
                course = course_detail.course
                # print(course)
                course.students += 1
                course.save()

                # TODO 购买的课程是否是永久有效
                pay_time_timestamp = order.pay_time.timestamp()

                # 如果用户购买的不是永久有效的课程
                if course_detail.expire > 0:
                    """代表不是永久有效的  开始处理课程剩余可观看的时间"""
                    expire = CourseExpire.objects.get(pk=course_detail.expire)
                    expire_timestamp = expire.expire_time * 24 * 60 * 60
                    # 当前时间 + 有效时间 = 最终的过期时间
                    end_time = datetime.fromtimestamp(pay_time_timestamp + expire_timestamp)
                else:
                    # 永久购买
                    end_time = None

                # TODO 为用户生成课程记录
                UserCourse.objects.create(
                    user_id=user.id,
                    course_id=course.id,
                    trade_no=data.get("trade_no"),
                    pay_time=order.pay_time,
                    out_time=end_time,
                )

                course_list.append({
                    "id": course.id,
                    "name": course.name
                })
        except:
            return Response({"message": "对不起，订单相关信息更新失败"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "支付成功",
                         "success": "success",
                         "pay_time": order.pay_time,
                         "real_price": order.real_price,
                         "course_list": course_list})
