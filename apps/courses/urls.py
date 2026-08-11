from django.urls import path

from .views import (
    CourseArchiveView,
    CourseDetailView,
    CourseListCreateView,
    CoursePublishView,
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
]