from django.urls import path

from .views import (
    EnrollmentCreateView,
    MyEnrollmentListView,
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
]