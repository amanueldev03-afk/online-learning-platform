from django.urls import path

from .views import (
    CompleteLessonView,
    MyProgressView,
    StartLessonProgressView,
    CourseProgressView,
)


app_name = "progress"


urlpatterns = [

    path(
        "lessons/<int:lesson_id>/start/",
        StartLessonProgressView.as_view(),
        name="lesson-start",
    ),

    path(
        "lessons/<int:lesson_id>/complete/",
        CompleteLessonView.as_view(),
        name="lesson-complete",
    ),

    path(
        "my/",
        MyProgressView.as_view(),
        name="my-progress",
    ),

    path(
        "courses/<int:course_id>/",
        CourseProgressView.as_view(),
        name="course-progress",
    ),
]