from django.urls import path, include
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('profile', ProfileViewSet, basename='profile')
router.register('course', CourseViewSet, basename='course')
router.register('module', ModuleViewSet, basename='module')
router.register('task', TaskViewSet, basename='task')
router.register('test_case', TestCaseViewSet, basename='test_case')
router.register('submission', SubmissionViewSet, basename='submission')


urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('logout/', LogoutView.as_view()),
]
