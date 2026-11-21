from django.contrib import admin
from .models import Course, CustomUser, Module, Task, TestCase

admin.site.register([CustomUser, Course, Module, Task, TestCase])