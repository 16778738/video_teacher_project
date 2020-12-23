from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView

from course import models
from course.models import Course, CourseChapter
from course.pagination import MyPagination
from course.serializers import CourseCategoryModelSerializer, CourseModelSerializer, CourseDetailModelSerializer, \
    CourseChapterModelSerializer


class CourseCategoryAPIView(ListAPIView):
    """课程分类信息查询"""
    queryset = models.CourseCategory.objects.filter(is_show=True, is_delete=False).order_by("orders")
    serializer_class = CourseCategoryModelSerializer


class CourseAPIView(ListAPIView):
    """课程信息展示"""
    queryset = models.Course.objects.filter(is_show=True, is_delete=False).order_by("orders")
    serializer_class = CourseModelSerializer
    # 根据不同的分类id来展示查询对应的课程
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    # 指定查询的字段
    filter_fields = ("course_category",)
    # 指定课程可以排序的条件
    ordering_fields = ("id", "students", "price")
    # 指定分页的类
    pagination_class = MyPagination


class CourseDetailAPIView(RetrieveAPIView):
    '''查询单个课程详情的信息'''
    queryset = Course.objects.filter(is_show=True, is_delete=False).order_by("orders")
    serializer_class = CourseDetailModelSerializer


class CourseLessonAPIView(ListAPIView):
    '''课程章节 课程章节对应的课时'''
    queryset = CourseChapter.objects.filter(is_show=True, is_delete=False).order_by("id")
    serializer_class = CourseChapterModelSerializer
    # 根据不同的分类id来展示查询对应的课程
    filter_backends = [DjangoFilterBackend]
    # 指定查询的字段
    filter_fields = ["course"]
