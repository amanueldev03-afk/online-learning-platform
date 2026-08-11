from django.utils import timezone

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .models import (
    Course,
    CourseSection,
    Lesson,
)
from .permissions import (
    IsCourseOwnerOrAdmin,
    IsInstructor,
    IsSectionOwnerOrAdmin,
    IsLessonOwnerOrAdmin,
)

from .services import (
    CoursePublishError,
    archive_course,
    publish_course,
)

from .serializers import (
    CourseSectionSerializer,
    CourseSerializer,
    LessonSerializer,
    CourseCurriculumSerializer,

)

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



class CoursePublishView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, pk):

        try:
            course = Course.objects.get(pk=pk)

        except Course.DoesNotExist:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            request.user.role != User.Role.ADMIN
            and course.instructor_id != request.user.id
        ):
            return Response(
                {
                    "detail": (
                        "You can only publish "
                        "your own courses."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            course = publish_course(course)

        except CoursePublishError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            CourseSerializer(course).data,
            status=status.HTTP_200_OK,
        )



class CourseArchiveView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, pk):

        try:
            course = Course.objects.get(pk=pk)

        except Course.DoesNotExist:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            request.user.role != User.Role.ADMIN
            and course.instructor_id != request.user.id
        ):
            return Response(
                {
                    "detail": (
                        "You can only archive "
                        "your own courses."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        course = archive_course(course)

        return Response(
            CourseSerializer(course).data,
            status=status.HTTP_200_OK,
        )




class CourseSectionListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, course_id):

        course = Course.objects.filter(
            id=course_id,
        ).first()

        if not course:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        sections = (
            CourseSection.objects
            .filter(course=course)
            .order_by("order", "created_at")
        )

        serializer = CourseSectionSerializer(
            sections,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, course_id):

        course = Course.objects.filter(
            id=course_id,
        ).first()

        if not course:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == User.Role.ADMIN:
            allowed = True
        elif (
            request.user.role == User.Role.INSTRUCTOR
            and course.instructor_id == request.user.id
        ):
            allowed = True
        else:
            allowed = False

        if not allowed:
            return Response(
                {
                    "detail": (
                        "You can only manage sections "
                        "of your own courses."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CourseSectionSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        section = serializer.save(
            course=course,
        )

        return Response(
            CourseSectionSerializer(section).data,
            status=status.HTTP_201_CREATED,
        )




class CourseSectionDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get_object(self, pk):

        return (
            CourseSection.objects
            .select_related("course")
            .filter(pk=pk)
            .first()
        )

    def get(self, request, pk):

        section = self.get_object(pk)

        if not section:
            return Response(
                {
                    "detail": "Section not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CourseSectionSerializer(
            section,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):

        section = self.get_object(pk)

        if not section:
            return Response(
                {
                    "detail": "Section not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = IsSectionOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            section,
        ):
            return Response(
                {
                    "detail": (
                        "You cannot modify this section."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CourseSectionSerializer(
            section,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):

        section = self.get_object(pk)

        if not section:
            return Response(
                {
                    "detail": "Section not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = IsSectionOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            section,
        ):
            return Response(
                {
                    "detail": (
                        "You cannot delete this section."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        section.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )



class LessonListCreateView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, section_id):

        section = (
            CourseSection.objects
            .select_related("course")
            .filter(id=section_id)
            .first()
        )

        if not section:
            return Response(
                {
                    "detail": "Section not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        lessons = (
            Lesson.objects
            .filter(section=section)
            .order_by("order", "created_at")
        )

        serializer = LessonSerializer(
            lessons,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request, section_id):

        section = (
            CourseSection.objects
            .select_related("course")
            .filter(id=section_id)
            .first()
        )

        if not section:
            return Response(
                {
                    "detail": "Section not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == User.Role.ADMIN:
            allowed = True

        elif (
            request.user.role == User.Role.INSTRUCTOR
            and section.course.instructor_id
            == request.user.id
        ):
            allowed = True

        else:
            allowed = False

        if not allowed:
            return Response(
                {
                    "detail": (
                        "You can only manage lessons "
                        "in your own courses."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = LessonSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        lesson = serializer.save(
            section=section,
        )

        return Response(
            LessonSerializer(lesson).data,
            status=status.HTTP_201_CREATED,
        )



class LessonDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get_object(self, pk):

        return (
            Lesson.objects
            .select_related(
                "section",
                "section__course",
            )
            .filter(pk=pk)
            .first()
        )

    def get(self, request, pk):

        lesson = self.get_object(pk)

        if not lesson:
            return Response(
                {
                    "detail": "Lesson not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        course = lesson.section.course

        # Published lessons can be viewed by learners.
        if (
            lesson.is_published
            and course.status == Course.Status.PUBLISHED
        ):
            return Response(
                LessonSerializer(lesson).data,
                status=status.HTTP_200_OK,
            )

        # Owner and admin can view unpublished lessons.
        if (
            request.user.role == User.Role.ADMIN
            or (
                request.user.role
                == User.Role.INSTRUCTOR
                and course.instructor_id
                == request.user.id
            )
        ):
            return Response(
                LessonSerializer(lesson).data,
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "detail": "Lesson not found."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    def patch(self, request, pk):

        lesson = self.get_object(pk)

        if not lesson:
            return Response(
                {
                    "detail": "Lesson not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = IsLessonOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            lesson,
        ):
            return Response(
                {
                    "detail": (
                        "You cannot modify this lesson."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = LessonSerializer(
            lesson,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):

        lesson = self.get_object(pk)

        if not lesson:
            return Response(
                {
                    "detail": "Lesson not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        permission = IsLessonOwnerOrAdmin()

        if not permission.has_object_permission(
            request,
            self,
            lesson,
        ):
            return Response(
                {
                    "detail": (
                        "You cannot delete this lesson."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        lesson.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class CourseCurriculumView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):

        course = (
            Course.objects
            .filter(
                pk=pk,
                status=Course.Status.PUBLISHED,
            )
            .select_related("instructor")
            .prefetch_related(
                "sections__lessons"
            )
            .first()
        )

        if not course:
            return Response(
                {
                    "detail": "Course not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CourseCurriculumSerializer(
            course
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )