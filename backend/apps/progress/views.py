from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.courses.models import Lesson

from .models import LessonProgress
from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from .serializers import LessonProgressSerializer
from .services import (
    ProgressError,
    complete_lesson,
    start_lesson,
    get_course_progress,
)

class StartLessonProgressView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, lesson_id):

        if request.user.role != User.Role.LEARNER:
            return Response(
                {
                    "detail": (
                        "Only learners can "
                        "track progress."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        lesson = (
            Lesson.objects
            .select_related(
                "section",
                "section__course",
            )
            .filter(
                id=lesson_id,
                section__course__status=(
                    "PUBLISHED"
                ),
            )
            .first()
        )

        if not lesson:
            return Response(
                {
                    "detail": "Lesson not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            progress = start_lesson(
                learner=request.user,
                lesson=lesson,
            )

        except ProgressError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            LessonProgressSerializer(
                progress
            ).data,
            status=status.HTTP_200_OK,
        )



class CompleteLessonView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, lesson_id):

        if request.user.role != User.Role.LEARNER:
            return Response(
                {
                    "detail": (
                        "Only learners can "
                        "track progress."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        lesson = (
            Lesson.objects
            .select_related(
                "section",
                "section__course",
            )
            .filter(
                id=lesson_id,
                section__course__status=(
                    "PUBLISHED"
                ),
            )
            .first()
        )

        if not lesson:
            return Response(
                {
                    "detail": "Lesson not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            progress = complete_lesson(
                learner=request.user,
                lesson=lesson,
            )

        except ProgressError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(
            LessonProgressSerializer(
                progress
            ).data,
            status=status.HTTP_200_OK,
        )


class MyProgressView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):

        if request.user.role != User.Role.LEARNER:
            return Response(
                {
                    "detail": (
                        "Only learners have "
                        "learning progress."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        progress = (
            LessonProgress.objects
            .filter(
                learner=request.user,
            )
            .select_related(
                "lesson",
                "lesson__section",
                "lesson__section__course",
            )
        )

        serializer = LessonProgressSerializer(
            progress,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class CourseProgressView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, course_id):

        if request.user.role != User.Role.LEARNER:
            return Response(
                {
                    "detail": (
                        "Only learners have "
                        "course progress."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        course = Course.objects.filter(
            id=course_id,
            status=Course.Status.PUBLISHED,
        ).first()

        if not course:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        enrolled = Enrollment.objects.filter(
            learner=request.user,
            course=course,
            status__in=[
                Enrollment.Status.ACTIVE,
                Enrollment.Status.COMPLETED,
            ],
        ).exists()

        if not enrolled:
            return Response(
                {
                    "detail": (
                        "You are not enrolled "
                        "in this course."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        progress = get_course_progress(
            learner=request.user,
            course=course,
        )

        return Response(
            progress,
            status=status.HTTP_200_OK,
        )