from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from drf_spectacular.utils import extend_schema

from apps.accounts.models import User
from apps.courses.models import Course

from .models import Enrollment
from .serializers import EnrollmentSerializer
from .services import (
    EnrollmentError,
    enroll_learner,
)


class EnrollmentCreateView(APIView):
    serializer_class = EnrollmentSerializer

    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        operation_id="create_enrollment",
        description="Enroll in a course (learner only)",
        request=EnrollmentSerializer,
        responses={201: EnrollmentSerializer}
    )
    def post(self, request):
        if request.user.role != User.Role.LEARNER:
            return Response(
                {
                    "detail": (
                        "Only learners can enroll "
                        "in courses."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        course_id = request.data.get("course")

        if not course_id:
            return Response(
                {
                    "course": (
                        "Course ID is required."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = Course.objects.filter(id=course_id).first()

        if not course:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            enrollment = enroll_learner(
                learner=request.user,
                course=course,
            )
        except EnrollmentError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            EnrollmentSerializer(enrollment).data,
            status=status.HTTP_201_CREATED,
        )


class MyEnrollmentListView(ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [
        IsAuthenticated,
    ]

    @extend_schema(
        operation_id="list_my_enrollments",
        description="List current user's enrollments (learner only)",
        responses={200: EnrollmentSerializer(many=True)}
    )
    def get_queryset(self):
        if self.request.user.role != User.Role.LEARNER:
            return Enrollment.objects.none()

        return (
            Enrollment.objects
            .filter(learner=self.request.user)
            .select_related("course")
        )
