from .models import *
from rest_framework.serializers import ModelSerializer, PrimaryKeyRelatedField, SerializerMethodField
from rest_framework import serializers

class RegisterSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        Profile.objects.create(user=user)
        return user


class ProfileSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'user', 'first_name', 'last_name', 'phone', 'birth_date', 'avatar']
        read_only_fields = ['id', 'user']


class UserSerializer(ModelSerializer):
    first_name = serializers.CharField(source='profile.first_name')
    last_name = serializers.CharField(source='profile.last_name')

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name']


class TaskNestedSerializer(ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'task_type', 'point', 'order']


class ModuleSerializer(ModelSerializer):
    tasks = TaskNestedSerializer(many=True, read_only=True)
    course_id = PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True
    )
    class Meta:
        model = Module
        fields = ['id', 'course_id', 'title', 'description', 'order', 'tasks']
        read_only_fields = ['id']


class CourseSerializer(ModelSerializer):
    teacher = UserSerializer(read_only=True)
    teacher_id = PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='teacher'),
        source='teacher',
        write_only=True
    )
    students = UserSerializer(many=True, read_only=True)
    student_ids = PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role='student'),
        source='students',
        many=True,
        write_only=True,
        required=False
    )
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'photo', 'teacher', 'teacher_id', 
                'students', 'student_ids', 'modules', 'created_at', 'is_active']
        read_only_fields = ['id', 'created_at', 'is_active']


class TaskSerializer(ModelSerializer):
    is_solved_by_me = SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'task_type',
        'starter_code', 'point', 'order', 'is_solved_by_me']

    def get_is_solved_by_me(self, obj):
        user = self.context['request'].user

        return Submission.objects.filter(
            user=user,
            task=obj,
            status='accepted'
        ).exists()


class TestCaseSerializer(ModelSerializer):
    task = TaskNestedSerializer(read_only=True)
    task_id = PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        source='task',
        write_only=True
    )
    class Meta:
        model = TestCase
        fields = ['id', 'task', 'task_id', 'input_data', 'expected_output', 'is_hidden']
        read_only_fields = ['id', 'task']


class SubmissionSerializer(ModelSerializer):
    task = TaskNestedSerializer(read_only=True)
    task_id = PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        source='task',
        write_only=True
    )
    class Meta:
        model = Submission
        fields = ['id', 'task', 'task_id', 'code', 'status', 'score', 'submitted_at']
        read_only_fields = ['id', 'task', 'status', 'score', 'submitted_at']