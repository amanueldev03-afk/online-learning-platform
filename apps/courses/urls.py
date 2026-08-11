from django.urls import path

from .views import (
    CourseArchiveView,
    CourseDetailView,
    CourseListCreateView,
    CoursePublishView,
    CourseSectionDetailView,
    CourseSectionListCreateView,
    LessonDetailView,
    LessonListCreateView,
)


app_name = "courses"


urlpatterns = [
    path(
        "",
        CourseListCreateView.as_view(),
        name="course-list-create",
    ),

    path(
        "<int:pk>/",
        CourseDetailView.as_view(),
        name="course-detail",
    ),
    path(
        "<int:pk>/publish/",
        CoursePublishView.as_view(),
        name="course-publish",
),

    path(
        "<int:pk>/archive/",
        CourseArchiveView.as_view(),
        name="course-archive",
    ),
    path(
        "<int:course_id>/sections/",
        CourseSectionListCreateView.as_view(),
        name="section-list-create",
    ),

    path(
        "sections/<int:pk>/",
        CourseSectionDetailView.as_view(),
        name="section-detail",
    ),
    path(
    "sections/<int:section_id>/lessons/",
    LessonListCreateView.as_view(),
    name="lesson-list-create",
),

    path(
        "lessons/<int:pk>/",
        LessonDetailView.as_view(),
        name="lesson-detail",
    ),
]