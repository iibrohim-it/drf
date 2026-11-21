from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ROLE = [
        ('user', 'User'),
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    role = models.CharField(max_length=150, choices=ROLE, default='user')

    def __str__(self):
        return self.username
    

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=17, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    def __str__(self):
        return f'{self.first_name} - {self.last_name}'


class Course(models.Model):
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='teaching_courses')
    students = models.ManyToManyField(CustomUser, related_name='enrolled_courses', blank=True)
    title = models.CharField(max_length=150)
    description = models.TextField()
    photo = models.ImageField(upload_to='course_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=150)
    description = models.TextField()
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title


class Task(models.Model):
    TASK_TYPES = [
        ('class_task', 'Class Task'),
        ('home_task', 'Home Task'),
        ('extra_task', 'Extra Task'),
    ]
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=150)
    description = models.TextField()
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, default='class_task')
    starter_code = models.TextField(blank=True)
    point = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title


class TestCase(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField()
    expected_output = models.TextField()
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return f'TestCase - {self.task.title}'


class Submission(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('wrong_answer', 'Wrong Answer'),
        ('error', 'Error'),
        ('time_limit', 'Time Limit'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='submissions')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS, default='pending')
    score = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.task.title}'