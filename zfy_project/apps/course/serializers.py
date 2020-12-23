from rest_framework.serializers import ModelSerializer

from course.models import CourseCategory, Course, Teacher, CourseLesson, CourseChapter


class CourseCategoryModelSerializer(ModelSerializer):
    class Meta:
        model = CourseCategory
        fields = ("id", "name")


class TeacherModelSerializer(ModelSerializer):
    class Meta:
        model = Teacher
        fields = ["id", "name", "title", "signature", "image", "brief"]


class CourseModelSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "name", "course_img", "students", "lessons", "pub_lessons", "price",
                  "teacher", "lesson_list", "discount_name", "real_price")


class CourseDetailModelSerializer(ModelSerializer):
    """提供课程详情所需的信息"""
    # 序列化器嵌套多表查询
    teacher = TeacherModelSerializer()

    class Meta:
        model = Course
        fields = ("id", "name", "course_img", "students", "lessons", "pub_lessons", "price",
                  "level_name", "teacher", "course_video", "active_time", "discount_name", "real_price")


class CourseLessonModelSerializer(ModelSerializer):
    class Meta:
        model = CourseLesson
        fields = ("id", "name", "free_trail", "duration")


class CourseChapterModelSerializer(ModelSerializer):
    """课程章节  课程章节对应的课时"""
    # 如果查询时是一对多的关系 需要指定参数 many =True
    coursesections = CourseLessonModelSerializer(many=True)

    class Meta:
        model = CourseChapter
        fields = ("id", "chapter", "name", "coursesections")
