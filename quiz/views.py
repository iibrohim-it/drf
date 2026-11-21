from .models import *
from .serializers import *
from .permissions import *
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
import subprocess
import sys


class RegisterView(CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        refresh = request.data.get("refresh")

        if not refresh:
            return Response({"detail": "refresh is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh).blacklist()
        except TokenError:
            return Response({"detail": "Invalid or expired token!"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ProfileViewSet(ModelViewSet):
    serializer_class = ProfileSerializer
    permission_classes = [IsOwner]

    http_method_names = ['get', 'patch', 'put', 'delete']

    def get_queryset(self):
        return Profile.objects.filter(user=self.request.user)


class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        queryset = Course.objects.select_related('teacher'
                ).prefetch_related('students', 'modules')

        if user.is_staff:
            return queryset

        if user.role == 'teacher':
            return queryset.filter(teacher=user)
  
        if user.role == 'student':
            return queryset.filter(students=user)

        return Course.objects.none()


class ModuleViewSet(ModelViewSet):
    serializer_class = ModuleSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        queryset = Module.objects.select_related('course'
                        ).prefetch_related('tasks')

        if user.is_staff:
            return queryset

        if user.role == 'teacher':
            return queryset.filter(course__teacher=user)

        if user.role == 'student':
            return queryset.filter(course__students=user)

        return Module.objects.none()


class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        queryset = Task.objects.select_related(
            'module', 'module__course')

        if user.is_staff:
            return queryset

        if user.role == 'teacher':
            return queryset.filter(module__course__teacher=user)

        if user.role == 'student':
            return queryset.filter(module__course__students=user)

        return Task.objects.none()


class TestCaseViewSet(ModelViewSet):
    serializer_class = TestCaseSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        user = self.request.user

        queryset = TestCase.objects.select_related(
            'task', 'task__module', 'task__module__course')

        if user.is_staff:
            return queryset

        if user.role == 'teacher':
            return queryset.filter(task__module__course__teacher=user)

        return TestCase.objects.none()


class SubmissionViewSet(ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user
                ).select_related('task')


    @action(detail=False, methods=['post'])
    def run(self, request):
        if request.user.role != 'student':
            return Response({'error' : 'Only students can run code!'}, status=403)

        task_id = request.data.get('task_id')
        code = request.data.get('code')
        input_data = request.data.get('input_data', '')

        if not task_id or not code:
            return Response({'error': 'task_id or code is required!'}, status=400)

        try:
            Task.objects.get(id=task_id, module__course__students=request.user)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found!'}, status=404)

        try:
            result = subprocess.run(
                [sys.executable, '-I', '-c', code],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=20
            )
            return Response({
                'output': result.stdout,
                'error': result.stderr,
                'status': 'success' if result.returncode == 0 else 'error'
            })

        except subprocess.TimeoutExpired:
            return Response({
                'status': 'time_limit',
                'output': '',
                'error': 'Time limit exceeded'
            })

    def create(self, request):
        if request.user.role != 'student':
            return Response({'error' : 'Only students can run code!'}, status=403)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task = serializer.validated_data['task']
        code = serializer.validated_data['code']

        if not task.module.course.students.filter(id=request.user.id).exists():
            return Response(
                {'error': 'You are not enrolled in this course!'},
                status=403)
        test_cases = task.test_cases.all()
        if not test_cases.exists():
            return Response({'error': 'This task has no test cases!'}, status=400)

        submission_status = 'accepted'
        score = task.point

        for test in test_cases:
            try:
                result = subprocess.run(
                    [sys.executable, '-I', '-c', code],
                    input=test.input_data,
                    capture_output=True,
                    text=True,
                    timeout=20
                )
                
                if result.returncode != 0:
                    submission_status = 'error'
                    score = 0
                    break

                if result.stdout.strip() != test.expected_output.strip():
                    submission_status = 'wrong_answer'
                    score = 0
                    break

            except subprocess.TimeoutExpired:
                submission_status = 'time_limit'
                score = 0
                break

        submission = serializer.save(
            user=request.user,
            status=submission_status,
            score=score)
        return Response(self.get_serializer(submission).data, status=201)