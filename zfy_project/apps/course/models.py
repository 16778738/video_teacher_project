from datetime import datetime

from django.db import models
from home.baseModel import BaseModel


class CourseCategory(BaseModel):
    """
    课程分类
    """
    name = models.CharField(max_length=64, unique=True, verbose_name="分类名称")

    class Meta:
        db_table = "bz_course_category"
        verbose_name = "课程分类"
        verbose_name_plural = "课程分类"

    def __str__(self):
        return "%s" % self.name


class Course(BaseModel):
    """
    课程信息
    """
    course_type = (
        (0, '收费课程'),
        (1, '高级课程'),
        (2, '专业技能')
    )
    level_choices = (
        (0, '入门'),
        (1, '进阶'),
        (2, '大师'),
    )
    status_choices = (
        (0, '上线'),
        (1, '下线'),
        (2, '预上线'),
    )

    course_video = models.FileField(upload_to="video", null=True, blank=True, verbose_name="视频")

    name = models.CharField(max_length=128, verbose_name="课程名称")
    course_img = models.ImageField(upload_to="course", max_length=255, verbose_name="封面图片", blank=True, null=True)
    course_type = models.SmallIntegerField(choices=course_type, default=0, verbose_name="付费类型")
    # 使用这个字段的原因
    brief = models.TextField(max_length=2048, verbose_name="详情介绍", null=True, blank=True)
    level = models.SmallIntegerField(choices=level_choices, default=1, verbose_name="难度等级")
    pub_date = models.DateField(verbose_name="发布日期", auto_now_add=True)
    period = models.IntegerField(verbose_name="建议学习周期(day)", default=7)
    file_path = models.FileField(max_length=128, verbose_name="课件路径", blank=True, null=True)
    status = models.SmallIntegerField(choices=status_choices, default=0, verbose_name="课程状态")
    course_category = models.ForeignKey("CourseCategory", on_delete=models.CASCADE, null=True, blank=True,
                                        verbose_name="课程分类")
    students = models.IntegerField(verbose_name="学习人数", default=0)
    lessons = models.IntegerField(verbose_name="总课时数量", default=0)
    pub_lessons = models.IntegerField(verbose_name="课时更新数量", default=0)
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="课程原价", default=0)
    teacher = models.ForeignKey("Teacher", on_delete=models.DO_NOTHING, null=True, blank=True, verbose_name="授课老师")

    @property
    def lesson_list(self):
        """获取当前课程的前几节课时用于展示"""
        lesson_list = CourseLesson.objects.filter(is_show=True, is_delete=False, course_id=self.id).all()

        data_list = []

        for lesson in lesson_list:
            data_list.append({
                "id": lesson.id,
                "name": lesson.name,
                "free_trail": lesson.free_trail
            })
        return data_list

    @property
    def level_name(self):
        # 自定义字段 返回课程对应的难度等级
        return self.level_choices[self.level][1]

    def active_list(self):
        active_list = self.activeprices.filter(is_show=True, is_delete=False,
                                               active__start_time__lte=datetime.now(),
                                               active__end_time__gte=datetime.now()).order_by("orders")
        return active_list

    @property
    def discount_name(self):
        """如果课程参与了活动，则获取当前课程所参与的课程的活动名称"""
        name = ""
        # 获取当前课程所参与的活动列表
        # 判断当前课程所参与的活动是否在时间范围内  活动开始时间必须小于当前时间  活动结束时间必须大于当前时间
        active_list = self.active_list()
        if len(active_list) > 0:
            """当前课程参与了优惠活动才返回活动名称"""
            active = active_list[0]
            name = active.discount.discount_type.name
        return name

    def real_price(self):
        """计算课程的真实价格"""
        price = self.price
        # 找到当前课程所参与的活动
        active_list = self.active_list()
        if len(active_list) > 0:
            """如果课程参与了活动，则根据课程所参与的活动计算价格"""
            active = active_list[0]
            # 判断课程价格的原价是否满足优惠条件的门槛
            condition = active.discount.condition
            # 获取活动的优惠公式
            sale = active.discount.sale
            self.price = float(self.price)
            if self.price >= condition:
                # 判断当前课程满足哪一种优惠条件
                if sale == "":
                    # 限时免费
                    price = 0
                elif sale[0] == "*":
                    # 限时折扣
                    price = self.price * float(sale[1:])
                elif sale[0] == "-":
                    # x限时减免
                    price = self.price - float(sale[1:])

                elif sale[0] == "满":
                    """
                    满减
                    500-80  400-40 300-20 200-10
                    """
                    split = sale.split("\r\n")
                    # 把满足条件的公式放入列表
                    sale_list = []
                    for item in split:
                        sale_item = item[1:]
                        # 门槛价  优惠价
                        condition_price, condition_sale = sale_item.split("-")
                        if self.price >= float(condition_price):
                            sale_list.append(float(condition_sale))

                    if len(sale_list) > 0:
                        # 课程原价减去当前满足条件中最高的优惠价格
                        price = self.price - max(sale_list)

        return price

    def real_expire_price(self, expire_id):
        """
        计算有效期参与活动的价格
        1. 先判断当前课程有效期id是否大于0    大于0则需要处理有效期
        2. 先根据有效期找到有效期对应的 原价
        3. 根据有效期的原价进行优惠活动的处理
        4. 根据不同活动的计算规则计算出对应的优惠的后的价格即可
        :return:
        """
        expire_price = CourseExpire.objects.get(pk=expire_id).price
        price = expire_price
        self.price = expire_price
        # 找到当前课程所参与的活动
        active_list = self.active_list()
        if len(active_list) > 0:
            """如果课程参与了活动，则根据课程所参与的活动计算价格"""
            active = active_list[0]
            # 判断课程价格的原价是否满足优惠条件的门槛
            condition = active.discount.condition
            # 获取活动的优惠公式
            sale = active.discount.sale
            self.price = float(self.price)
            if self.price >= condition:
                # 判断当前课程满足哪一种优惠条件
                if sale == "":
                    # 限时免费
                    price = 0
                elif sale[0] == "*":
                    # 限时折扣
                    price = self.price * float(sale[1:])
                elif sale[0] == "-":
                    # x限时减免
                    price = self.price - float(sale[1:])

                elif sale[0] == "满":
                    """
                    满减
                    500-80  400-40 300-20 200-10
                    """
                    split = sale.split("\r\n")
                    # 把满足条件的公式放入列表
                    sale_list = []
                    for item in split:
                        sale_item = item[1:]
                        # 门槛价  优惠价
                        condition_price, condition_sale = sale_item.split("-")
                        if self.price >= float(condition_price):
                            sale_list.append(float(condition_sale))

                    if len(sale_list) > 0:
                        # 课程原价减去当前满足条件中最高的优惠价格
                        price = self.price - max(sale_list)

        return price


    @property
    def active_time(self):
        """返回活动剩余时间"""
        time = 0
        active_list = self.active_list()

        if len(active_list) > 0:
            active = active_list[0]
            # 获取当前服务器的时间戳
            now_time = datetime.now().timestamp()
            # 获取活动结束的时间戳
            end_time = active.active.end_time.timestamp()
            time = end_time - now_time

            return int(time)

    @property
    def expire_text(self):
        """获取当前课程的有效期"""
        expires = self.course_expire.filter(is_show=True, is_delete=False)
        # print(expires,'当前有效期')
        data = []

        for item in expires:
            data.append({
                "id": item.id,
                "expire_text": item.expire_text,
                "price": item.price,
            })

        if self.price > 0:
            data.append({
                "id": 0,
                "expire_text": "永久有效",
                "price": self.price,
            })

        return data

    class Meta:
        db_table = "bz_course"
        verbose_name = "课程信息"
        verbose_name_plural = "课程信息"

    def __str__(self):
        return "%s" % self.name


class Teacher(BaseModel):
    """讲师、导师表"""
    role_choices = (
        (0, '讲师'),
        (1, '班主任'),
        (2, '教学总监'),
    )
    name = models.CharField(max_length=32, verbose_name="讲师title")
    role = models.SmallIntegerField(choices=role_choices, default=0, verbose_name="讲师身份")
    title = models.CharField(max_length=64, verbose_name="职称")
    signature = models.CharField(max_length=255, verbose_name="导师签名", help_text="导师签名", blank=True, null=True)
    image = models.ImageField(upload_to="teacher", null=True, verbose_name="讲师封面")
    brief = models.TextField(max_length=1024, verbose_name="讲师描述")

    class Meta:
        db_table = "bz_teacher"
        verbose_name = "讲师导师"
        verbose_name_plural = "讲师导师"

    def __str__(self):
        return "%s" % self.name


class CourseChapter(BaseModel):
    """课程章节"""
    course = models.ForeignKey("Course", related_name='coursechapters', on_delete=models.CASCADE, verbose_name="课程名称")
    chapter = models.SmallIntegerField(verbose_name="第几章", default=1)
    name = models.CharField(max_length=128, verbose_name="章节标题")
    summary = models.TextField(verbose_name="章节介绍", blank=True, null=True)
    pub_date = models.DateField(verbose_name="发布日期", auto_now_add=True)

    class Meta:
        db_table = "bz_course_chapter"
        verbose_name = "课程章节"
        verbose_name_plural = "课程章节"

    def __str__(self):
        return "%s:(第%s章)%s" % (self.course, self.chapter, self.name)


class CourseLesson(BaseModel):
    """课程课时"""
    section_type_choices = (
        (0, '文档'),
        (1, '练习'),
        (2, '视频')
    )
    chapter = models.ForeignKey("CourseChapter", related_name='coursesections', on_delete=models.CASCADE,
                                verbose_name="课程章节")
    name = models.CharField(max_length=128, verbose_name="课时标题")
    section_type = models.SmallIntegerField(default=2, choices=section_type_choices, verbose_name="课时种类")
    section_link = models.CharField(max_length=255, blank=True, null=True, verbose_name="课时链接",
                                    help_text="若是video，填vid,若是文档，填link")
    duration = models.CharField(verbose_name="视频时长", blank=True, null=True, max_length=32)  # 仅在前端展示使用
    pub_date = models.DateTimeField(verbose_name="发布时间", auto_now_add=True)
    free_trail = models.BooleanField(verbose_name="是否可试看", default=False)
    course = models.ForeignKey("Course", related_name="course_lesson", on_delete=models.CASCADE, verbose_name="课程")
    is_show_list = models.BooleanField(verbose_name="是否展示到课程", default=False)

    class Meta:
        db_table = "bz_course_lesson"
        verbose_name = "课程课时"
        verbose_name_plural = "课程课时"

    def __str__(self):
        return "%s-%s" % (self.chapter, self.name)


class CourseDiscountType(BaseModel):
    """课程优惠类型"""
    name = models.CharField(max_length=32, verbose_name="优惠类型名称")
    remark = models.CharField(max_length=250, blank=True, null=True, verbose_name="备注信息")

    class Meta:
        db_table = "bz_course_discount_type"
        verbose_name = "课程优惠类型"
        verbose_name_plural = "课程优惠类型"

    def __str__(self):
        return "%s" % (self.name)


class CourseDiscount(BaseModel):
    """课程优惠折扣模型"""
    discount_type = models.ForeignKey("CourseDiscountType", on_delete=models.CASCADE, related_name='coursediscounts',
                                      verbose_name="优惠类型")
    # 参与优惠的门槛
    condition = models.IntegerField(blank=True, default=0, verbose_name="满足优惠的价格条件",
                                    help_text="设置参与优惠的价|格门槛，表示商品必须在xx价格以上的时候才参与优惠活动，<br>如果不填，则不设置门槛")
    # 优惠公式
    sale = models.TextField(verbose_name="优惠公式", blank=True, null=True, help_text="""
    不填表示免费；<br>
    *号开头表示折扣价，例如*0.82表示八二折；<br>
    -号开头则表示减免，例如-20表示原价-20；<br>
    如果需要表示满减,则需要使用 原价-优惠价格,例如表示课程价格大于100,优惠10;大于200,优惠20,格式如下:<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;满100-10<br>
    &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;满200-25<br>
    """)

    class Meta:
        db_table = "bz_course_discount"
        verbose_name = "价格优惠策略"
        verbose_name_plural = "价格优惠策略"

    def __str__(self):
        return "价格优惠:%s,优惠条件:%s,优惠值:%s" % (self.discount_type.name, self.condition, self.sale)


class Activity(BaseModel):
    """优惠活动时间"""
    name = models.CharField(max_length=150, verbose_name="活动名称")
    start_time = models.DateTimeField(verbose_name="优惠策略的开始时间")
    end_time = models.DateTimeField(verbose_name="优惠策略的结束时间")
    remark = models.CharField(max_length=250, blank=True, null=True, verbose_name="备注信息")

    class Meta:
        db_table = "bz_activity"
        verbose_name = "商品活动"
        verbose_name_plural = "商品活动"

    def __str__(self):
        return self.name


class CoursePriceDiscount(BaseModel):
    """课程与优惠策略的关系表"""
    course = models.ForeignKey("Course", on_delete=models.CASCADE, related_name="activeprices", verbose_name="课程")
    active = models.ForeignKey("Activity", on_delete=models.DO_NOTHING, related_name="activecourses", verbose_name="活动")
    discount = models.ForeignKey("CourseDiscount", on_delete=models.CASCADE, related_name="discountcourse",
                                 verbose_name="优惠折扣")

    class Meta:
        db_table = "bz_course_price_discount"
        verbose_name = "课程与优惠策略的关系表"
        verbose_name_plural = "课程与优惠策略的关系表"

    def __str__(self):
        return "课程：%s，优惠活动: %s,开始时间:%s,结束时间:%s" % (
            self.course.name, self.active.name, self.active.start_time, self.active.end_time)


class CourseExpire(BaseModel):
    """课程有效期模型"""
    course = models.ForeignKey("Course", related_name='course_expire', on_delete=models.CASCADE,
                               verbose_name="课程名称")
    expire_time = models.IntegerField(verbose_name="有效期", null=True, blank=True, help_text="有效期按天数计算")
    expire_text = models.CharField(max_length=150, verbose_name="提示文本", null=True, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="课程价格", default=0)

    class Meta:
        db_table = "bz_course_expire"
        verbose_name = "课程有效期"
        verbose_name_plural = verbose_name

    def __str__(self):
        return "课程：%s，有效期：%s，价格：%s" % (self.course, self.expire_text, self.price)
