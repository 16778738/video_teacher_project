from django.db import models

# Create your models here.
from home.baseModel import BaseModel


class Banner(models.Model):
    '''
    轮播图
    '''
    img = models.ImageField(upload_to='banner', max_length=255, verbose_name="轮播图")
    title = models.CharField(max_length=200, verbose_name="图片标题")
    link = models.CharField(max_length=300, verbose_name="图片链接")
    is_show = models.BooleanField(default=False, verbose_name="图片是否展示")
    orders = models.IntegerField(default=1, verbose_name="图片排序")
    is_delete = models.BooleanField(default=False, verbose_name="是否删除")

    class Meta:
        db_table = "bz_banner"
        verbose_name = "轮播图"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title


class Nav(BaseModel):
    """
    导航图
    """
    POSITION_OPTION = (
        (1, "顶部导航"),
        (2, "底部导航"),
    )
    title = models.CharField(max_length=200, verbose_name="导航标题")
    link = models.CharField(max_length=300, verbose_name="导航链接")
    position = models.IntegerField(choices=POSITION_OPTION, default=1, verbose_name="导航位置")
    is_site = models.BooleanField(default=False, verbose_name="是否是外部链接")

    class Meta:
        db_table = "bz_nzv"
        verbose_name = "导航条"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title
