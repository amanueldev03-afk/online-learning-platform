from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .models import Course
from .permissions import (
    IsCourseOwnerOrAdmin,
    IsInstructor,
)
from .serializers import CourseSerializer


class CourseListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsInstructor()]

        return [AllowAny()]

    def get(self, request):
        courses = (
            Course.objects
            .filter(
                status=Course.Status.PUBLISHED
            )
            .select_related("instructor")
        )

        serializer = CourseSerializer(
            courses,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = CourseSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        course = serializer.save(
            instructor=request.user
        )

        return Response(
            CourseSerializer(course).data,
            status=status.HTTP_201_CREATED,
        )


class CourseDetailView(APIView):

    def get_object(self, pk):
        try:
            return Course.objects.select_related(
                "instructor"
            ).get(pk=pk)

        except Course.DoesNotExist:
            return None

    def get(self, request, pk):

        course = self.get_object(pk)

        if not course:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # Public users can only view published courses.
        if course.status != Course.Status.PUBLISHED:

            if not request.user.is_authenticated:
                return Response(
                    {
                        "detail": "Course not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Only owner/admin can view unpublished course.
            if (
                request.user.role
                != User.Role.ADMIN
                and course.instructor_id
                != request.user.id
            ):
                return Response(
                    {
                        "detail": "Course not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = CourseSerializer(course)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):

        course = self.get_object(pk)

        if not course:
            return Response(
                {"detail": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = IsCourseOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            course,
        ):
            return Response(
                {"detail": "You cannot modify this course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CourseSerializer(
            course,
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):

        course = self.get_object(pk)

        if not course:
            return Response(
                {"detail": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = IsCourseOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            course,
        ):
            return Response(
                {"detail": "You cannot modify this course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CourseSerializer(
            course,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):

        course = self.get_object(pk)

        if not course:
            return Response(
                {"detail": "Course not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = IsCourseOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            course,
        ):
            return Response(
                {"detail": "You cannot delete this course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        course.delete()

        return Response(
            {
                "message": "Course deleted successfully."
            },
            status=status.HTTP_204_NO_CONTENT,
        )