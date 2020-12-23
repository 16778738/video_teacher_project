from django.db import models


class BaseModel(models.Model):
    '''
    基础表
    '''
    is_show = models.BooleanField(default=False, verbose_name="是否展示")
    orders = models.IntegerField(default=1, verbose_name="排序")
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    update_time = models.DateTimeField(auto_now=True, verbose_name="修改时间")

    class Meta:
        abstract = True