from django.urls import path

from .views import (
    EnrollmentCreateView,
    MyEnrollmentListView,
    LessonDetailView,
)


app_name = "enrollments"


urlpatterns = [
    path(
        "",
        EnrollmentCreateView.as_view(),
        name="enrollment-create",
    ),

    path(
        "my/",
        MyEnrollmentListView.as_view(),
        name="my-enrollments",
    ),

    path(
        "lessons/<int:pk>/",
        LessonDetailView.as_view(),
        name="lesson-detail",
    ),
]