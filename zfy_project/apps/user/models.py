from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class UserInfo(AbstractUser):
    '''
    用户模型
    '''
    phone = models.CharField(max_length=11, unique=True, verbose_name="用户手机号")
    user_head = models.ImageField(upload_to="user", verbose_name="用户头像", blank=True,
                                  null=True)  # blank表单可以为空,null数据库可以为空

    class Meta:
        db_table = "bz_user"
        verbose_name = "用户"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username
