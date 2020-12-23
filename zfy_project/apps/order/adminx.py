import xadmin

from order import models

xadmin.site.register(models.Order)
xadmin.site.register(models.OrderDetail)
