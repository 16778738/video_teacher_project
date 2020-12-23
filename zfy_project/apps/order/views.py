from django.db import transaction
from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework_jwt.utils import jwt_payload_handler
from order.models import Order
from order.serializer import OrderModelSerializer


class OrderAPIView(CreateAPIView):
    queryset = Order.objects.filter(is_delete=False, is_show=True)
    serializer_class = OrderModelSerializer


class DemoAPIView(CreateAPIView):

    # @transaction.atomic()   # 第二种方式  当方法执行完成后自动提交控制
    def post(self, request, *args, **kwargs):
        pass
        # 开启事务
        with transaction.atomic():
            # 记录事务回滚的点
            savepoint = transaction.savepoint()

            # 遇到异常时  可以回滚到上个事务点
            transaction.savepoint_rollback(savepoint)
