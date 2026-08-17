from django.utils import timezone
from django.db.models import Q
from drf_spectacular.utils import extend_schema
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

    @extend_schema(
        operation_id="list_courses",
        description="List all published courses with optional filtering",
        parameters=[
            {
                "name": "search",
                "required": False,
                "type": str,
                "description": "Search by title or description"
            },
            {
                "name": "category",
                "required": False,
                "type": str,
                "description": "Filter by category"
            },
            {
                "name": "level",
                "required": False,
                "type": str,
                "description": "Filter by level (BEGINNER, INTERMEDIATE, ADVANCED)"
            },
            {
                "name": "is_free",
                "required": False,
                "type": bool,
                "description": "Filter by free/paid status"
            }
        ],
        responses={200: CourseSerializer(many=True)}
    )
    def get(self, request):

        courses = (
            Course.objects
            .filter(
                status=Course.Status.PUBLISHED,
            )
            .select_related(
                "instructor",
                "category",
                "category__parent",
            )
        )

        search = request.query_params.get(
            "search"
        )

        category = request.query_params.get(
            "category"
        )

        category_slug = request.query_params.get(
            "category_slug"
        )

        level = request.query_params.get(
            "level"
        )

        language = request.query_params.get(
            "language"
        )

        is_free = request.query_params.get(
            "is_free"
        )

        if search:
            courses = courses.filter(
                Q(title__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
            )

        if category:
            courses = courses.filter(
                category_id=category
            )

        if category_slug:
            courses = courses.filter(
                category__slug=category_slug
            )

        if level:
            courses = courses.filter(
                level=level
            )

        if language:
            courses = courses.filter(
                language__iexact=language
            )

        if is_free is not None:
            courses = courses.filter(
                is_free=is_free.lower() == "true"
            )

        serializer = CourseSerializer(
            courses,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="create_course",
        description="Create a new course (instructor only)",
        request=CourseSerializer,
        responses={201: CourseSerializer}
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

    @extend_schema(
        operation_id="retrieve_course",
        description="Retrieve a specific course by ID",
        responses={200: CourseSerializer, 404: None}
    )
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

    @extend_schema(
        operation_id="update_course",
        description="Update a course completely (owner/admin only)",
        request=CourseSerializer,
        responses={200: CourseSerializer, 403: None, 404: None}
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

    @extend_schema(
        operation_id="partial_update_course",
        description="Update a course partially (owner/admin only)",
        request=CourseSerializer,
        responses={200: CourseSerializer, 403: None, 404: None}
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

    @extend_schema(
        operation_id="delete_course",
        description="Delete a course (owner/admin only)",
        responses={204: None, 403: None, 404: None}
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

    @extend_schema(
        operation_id="publish_course",
        description="Publish a course (owner/admin only)",
        responses={200: CourseSerializer, 400: None, 403: None, 404: None}
    )
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

    @extend_schema(
        operation_id="archive_course",
        description="Archive a course (owner/admin only)",
        responses={200: CourseSerializer, 403: None, 404: None}
    )
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

    @extend_schema(
        operation_id="list_sections",
        description="List all sections for a specific course",
        responses={200: CourseSectionSerializer(many=True), 404: None}
    )
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

    @extend_schema(
        operation_id="create_section",
        description="Create a new section for a course (owner/admin only)",
        request=CourseSectionSerializer,
        responses={201: CourseSectionSerializer, 403: None, 404: None}
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

    @extend_schema(
        operation_id="retrieve_section",
        description="Retrieve a specific section by ID",
        responses={200: CourseSectionSerializer, 404: None}
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

    @extend_schema(
        operation_id="partial_update_section",
        description="Update a section partially (owner/admin only)",
        request=CourseSectionSerializer,
        responses={200: CourseSectionSerializer, 403: None, 404: None}
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

    @extend_schema(
        operation_id="delete_section",
        description="Delete a section (owner/admin only)",
        responses={204: None, 403: None, 404: None}
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

    @extend_schema(
        operation_id="list_lessons",
        description="List all lessons for a specific section",
        responses={200: LessonSerializer(many=True), 404: None}
    )
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

    @extend_schema(
        operation_id="create_lesson",
        description="Create a new lesson for a section (owner/admin only)",
        request=LessonSerializer,
        responses={201: LessonSerializer, 403: None, 404: None}
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

    @extend_schema(
        operation_id="retrieve_lesson",
        description="Retrieve a specific lesson by ID",
        responses={200: LessonSerializer, 404: None}
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

    @extend_schema(
        operation_id="partial_update_lesson",
        description="Update a lesson partially (owner/admin only)",
        request=LessonSerializer,
        responses={200: LessonSerializer, 403: None, 404: None}
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

    @extend_schema(
        operation_id="delete_lesson",
        description="Delete a lesson (owner/admin only)",
        responses={204: None, 403: None, 404: None}
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

    @extend_schema(
        operation_id="course_curriculum",
        description="Get the full curriculum of a published course (sections and lessons)",
        responses={200: CourseCurriculumSerializer, 404: None}
    )
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