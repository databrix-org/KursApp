from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView
from . import views, accounts

router = DefaultRouter()
for name, view in [
    ("courses", views.CourseViewSet),
    ("modules", views.ModuleViewSet),
    ("lessons", views.LessonViewSet),
    ("groups", views.GroupViewSet),
    ("submissions", views.SubmissionViewSet),
    ("assets", views.AssetViewSet),
    ("tickets", views.TicketViewSet),
]:
    router.register(name, view, basename=name)
urlpatterns = [
    path("", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("session/", accounts.session),
    path("session/change/", accounts.session_change),
    path("invitations/", accounts.invitations),
    path("invitations/accept/", accounts.accept_invitation),
    path("session/verify/", accounts.verify_email),
    path("session/reset/", accounts.password_reset),
    path("session/reset-confirm/", accounts.password_reset_confirm),
    path("admin/announcements/", accounts.admin_announcement),
    path("users/", accounts.users_list),
    path("users/<int:pk>/", accounts.user_detail),
]
