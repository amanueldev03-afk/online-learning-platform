from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.accounts.models import User
from apps.categories.models import Category
from apps.courses.models import Course, CourseSection, Lesson
from apps.enrollments.models import Enrollment
from .models import LessonProgress
from .services import (
    ProgressError,
    start_lesson,
    complete_lesson,
    get_course_progress,
    update_enrollment_completion,
)


class LessonProgressModelTest(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
            role=User.Role.LEARNER
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            first_name="Jane",
            last_name="Smith",
            role=User.Role.INSTRUCTOR
        )
        
        self.category = Category.objects.create(
            name="Web Development",
            description="Web dev courses"
        )
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Masterclass",
            short_description="Learn React",
            description="Comprehensive React course",
            category=self.category,
            level=Course.Level.BEGINNER,
            price=49.99,
            is_free=False,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Getting Started",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="Introduction to React",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            duration_minutes=15,
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_lesson_progress_creation(self):
        progress = LessonProgress.objects.create(
            learner=self.learner,
            enrollment=self.enrollment,
            lesson=self.lesson,
            completed=False,
            started_at=timezone.now()
        )
        
        self.assertEqual(progress.learner, self.learner)
        self.assertEqual(progress.lesson, self.lesson)
        self.assertEqual(progress.enrollment, self.enrollment)
        self.assertFalse(progress.completed)
    
    def test_unique_learner_lesson_constraint(self):
        LessonProgress.objects.create(
            learner=self.learner,
            enrollment=self.enrollment,
            lesson=self.lesson,
            completed=False
        )
        
        with self.assertRaises(Exception):
            LessonProgress.objects.create(
                learner=self.learner,
                enrollment=self.enrollment,
                lesson=self.lesson,
                completed=False
            )
    
    def test_lesson_progress_str(self):
        progress = LessonProgress.objects.create(
            learner=self.learner,
            enrollment=self.enrollment,
            lesson=self.lesson
        )
        
        expected = f"{self.learner.email} - {self.lesson.title}"
        self.assertEqual(str(progress), expected)


class StartLessonServiceTest(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_start_lesson_success(self):
        progress = start_lesson(
            learner=self.learner,
            lesson=self.lesson
        )
        
        self.assertEqual(progress.learner, self.learner)
        self.assertEqual(progress.lesson, self.lesson)
        self.assertIsNotNone(progress.started_at)
        self.assertIsNotNone(progress.last_accessed_at)
        self.assertFalse(progress.completed)
    
    def test_start_lesson_without_enrollment(self):
        another_learner = User.objects.create_user(
            email="another@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        with self.assertRaises(ProgressError) as context:
            start_lesson(
                learner=another_learner,
                lesson=self.lesson
            )
        
        self.assertEqual(
            str(context.exception),
            "You are not enrolled in this course."
        )
    
    def test_start_lesson_already_started(self):
        start_lesson(learner=self.learner, lesson=self.lesson)
        
        progress = start_lesson(
            learner=self.learner,
            lesson=self.lesson
        )
        
        self.assertEqual(
            LessonProgress.objects.filter(
                learner=self.learner,
                lesson=self.lesson
            ).count(),
            1
        )


class CompleteLessonServiceTest(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_complete_lesson_success(self):
        start_lesson(learner=self.learner, lesson=self.lesson)
        
        progress = complete_lesson(
            learner=self.learner,
            lesson=self.lesson
        )
        
        self.assertTrue(progress.completed)
        self.assertIsNotNone(progress.completed_at)
        self.assertIsNotNone(progress.started_at)
    
    def test_complete_lesson_without_enrollment(self):
        another_learner = User.objects.create_user(
            email="another@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        with self.assertRaises(ProgressError) as context:
            complete_lesson(
                learner=another_learner,
                lesson=self.lesson
            )
        
        self.assertEqual(
            str(context.exception),
            "You are not enrolled in this course."
        )
    
    def test_complete_lesson_without_starting(self):
        with self.assertRaises(ProgressError) as context:
            complete_lesson(
                learner=self.learner,
                lesson=self.lesson
            )
        
        self.assertEqual(
            str(context.exception),
            "You must start the lesson before completing it."
        )
    
    def test_complete_already_completed_lesson(self):
        start_lesson(learner=self.learner, lesson=self.lesson)
        complete_lesson(learner=self.learner, lesson=self.lesson)
        
        progress = complete_lesson(
            learner=self.learner,
            lesson=self.lesson
        )
        
        self.assertTrue(progress.completed)
        self.assertIsNotNone(progress.completed_at)


class StartLessonProgressViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER,
            email_verified=True
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR,
            email_verified=True
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_start_lesson_as_learner(self):
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/start/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data)
        self.assertIn("lesson_title", response.data)
    
    def test_start_lesson_as_instructor_forbidden(self):
        self.client.force_authenticate(user=self.instructor)
        
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/start/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_start_lesson_unauthenticated(self):
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/start/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_start_lesson_not_found(self):
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.post(
            "/api/progress/lessons/99999/start/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_start_lesson_without_enrollment(self):
        another_learner = User.objects.create_user(
            email="another@example.com",
            password="testpass123",
            role=User.Role.LEARNER,
            email_verified=True
        )
        
        self.client.force_authenticate(user=another_learner)
        
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/start/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CompleteLessonViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER,
            email_verified=True
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR,
            email_verified=True
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_complete_lesson_as_learner(self):
        self.client.force_authenticate(user=self.learner)
        
        # Start lesson first
        self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/start/"
        )
        
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/complete/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["completed"])
        self.assertIsNotNone(response.data["completed_at"])
    
    def test_complete_lesson_as_instructor_forbidden(self):
        self.client.force_authenticate(user=self.instructor)
        
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/complete/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_complete_lesson_unauthenticated(self):
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/complete/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_complete_lesson_not_found(self):
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.post(
            "/api/progress/lessons/99999/complete/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_complete_lesson_without_starting(self):
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.post(
            f"/api/progress/lessons/{self.lesson.id}/complete/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            "must start the lesson before completing",
            response.data["detail"].lower()
        )


class MyProgressViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER,
            email_verified=True
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR,
            email_verified=True
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        
        self.progress = LessonProgress.objects.create(
            learner=self.learner,
            enrollment=self.enrollment,
            lesson=self.lesson,
            completed=True
        )
    
    def test_get_my_progress_as_learner(self):
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.get("/api/progress/my/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["lesson_title"], "React Basics")
    
    def test_get_my_progress_as_instructor_forbidden(self):
        self.client.force_authenticate(user=self.instructor)
        
        response = self.client.get("/api/progress/my/")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_my_progress_unauthenticated(self):
        response = self.client.get("/api/progress/my/")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_my_progress_empty(self):
        another_learner = User.objects.create_user(
            email="another@example.com",
            password="testpass123",
            role=User.Role.LEARNER,
            email_verified=True
        )
        
        self.client.force_authenticate(user=another_learner)
        
        response = self.client.get("/api/progress/my/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class GetCourseProgressServiceTest(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson1 = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video1.mp4",
            order=1,
            is_published=True
        )
        
        self.lesson2 = Lesson.objects.create(
            section=self.section,
            title="React Hooks",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video2.mp4",
            order=2,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_get_course_progress_zero_lessons(self):
        empty_course = Course.objects.create(
            instructor=self.instructor,
            title="Empty Course",
            short_description="No lessons",
            description="Empty",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        progress = get_course_progress(
            learner=self.learner,
            course=empty_course
        )
        
        self.assertEqual(progress["total_lessons"], 0)
        self.assertEqual(progress["completed_lessons"], 0)
        self.assertEqual(progress["progress_percentage"], 0.0)
        self.assertFalse(progress["is_completed"])
    
    def test_get_course_progress_no_completion(self):
        progress = get_course_progress(
            learner=self.learner,
            course=self.course
        )
        
        self.assertEqual(progress["total_lessons"], 2)
        self.assertEqual(progress["completed_lessons"], 0)
        self.assertEqual(progress["progress_percentage"], 0.0)
        self.assertFalse(progress["is_completed"])
    
    def test_get_course_progress_partial_completion(self):
        start_lesson(learner=self.learner, lesson=self.lesson1)
        complete_lesson(learner=self.learner, lesson=self.lesson1)
        
        progress = get_course_progress(
            learner=self.learner,
            course=self.course
        )
        
        self.assertEqual(progress["total_lessons"], 2)
        self.assertEqual(progress["completed_lessons"], 1)
        self.assertEqual(progress["progress_percentage"], 50.0)
        self.assertFalse(progress["is_completed"])
    
    def test_get_course_progress_full_completion(self):
        start_lesson(learner=self.learner, lesson=self.lesson1)
        complete_lesson(learner=self.learner, lesson=self.lesson1)
        start_lesson(learner=self.learner, lesson=self.lesson2)
        complete_lesson(learner=self.learner, lesson=self.lesson2)
        
        progress = get_course_progress(
            learner=self.learner,
            course=self.course
        )
        
        self.assertEqual(progress["total_lessons"], 2)
        self.assertEqual(progress["completed_lessons"], 2)
        self.assertEqual(progress["progress_percentage"], 100.0)
        self.assertTrue(progress["is_completed"])


class UpdateEnrollmentCompletionServiceTest(TestCase):
    def setUp(self):
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_update_enrollment_not_completed(self):
        result = update_enrollment_completion(
            enrollment=self.enrollment
        )
        
        self.assertFalse(result)
        self.enrollment.refresh_from_db()
        self.assertEqual(
            self.enrollment.status,
            Enrollment.Status.ACTIVE
        )
    
    def test_update_enrollment_completed(self):
        start_lesson(learner=self.learner, lesson=self.lesson)
        complete_lesson(learner=self.learner, lesson=self.lesson)
        
        result = update_enrollment_completion(
            enrollment=self.enrollment
        )
        
        self.assertTrue(result)
        self.enrollment.refresh_from_db()
        self.assertEqual(
            self.enrollment.status,
            Enrollment.Status.COMPLETED
        )
        self.assertIsNotNone(self.enrollment.completed_at)
    
    def test_update_enrollment_already_completed(self):
        start_lesson(learner=self.learner, lesson=self.lesson)
        complete_lesson(learner=self.learner, lesson=self.lesson)
        update_enrollment_completion(enrollment=self.enrollment)
        
        result = update_enrollment_completion(
            enrollment=self.enrollment
        )
        
        self.assertFalse(result)
        self.enrollment.refresh_from_db()
        self.assertEqual(
            self.enrollment.status,
            Enrollment.Status.COMPLETED
        )


class CourseProgressViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            role=User.Role.LEARNER,
            email_verified=True
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR,
            email_verified=True
        )
        
        self.category = Category.objects.create(name="Web Development")
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title="React Course",
            short_description="Learn React",
            description="React course",
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Introduction",
            order=1,
            is_published=True
        )
        
        self.lesson = Lesson.objects.create(
            section=self.section,
            title="React Basics",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video.mp4",
            order=1,
            is_published=True
        )
        
        self.enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
    
    def test_get_course_progress_as_learner(self):
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.get(
            f"/api/progress/courses/{self.course.id}/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("course_id", response.data)
        self.assertIn("course_title", response.data)
        self.assertIn("total_lessons", response.data)
        self.assertIn("completed_lessons", response.data)
        self.assertIn("progress_percentage", response.data)
        self.assertIn("is_completed", response.data)
    
    def test_get_course_progress_as_instructor_forbidden(self):
        self.client.force_authenticate(user=self.instructor)
        
        response = self.client.get(
            f"/api/progress/courses/{self.course.id}/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_course_progress_unauthenticated(self):
        response = self.client.get(
            f"/api/progress/courses/{self.course.id}/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_course_progress_not_found(self):
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.get("/api/progress/courses/99999/")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_course_progress_without_enrollment(self):
        another_learner = User.objects.create_user(
            email="another@example.com",
            password="testpass123",
            role=User.Role.LEARNER,
            email_verified=True
        )
        
        self.client.force_authenticate(user=another_learner)
        
        response = self.client.get(
            f"/api/progress/courses/{self.course.id}/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_course_progress_with_completion(self):
        start_lesson(learner=self.learner, lesson=self.lesson)
        complete_lesson(learner=self.learner, lesson=self.lesson)
        
        self.client.force_authenticate(user=self.learner)
        
        response = self.client.get(
            f"/api/progress/courses/{self.course.id}/"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_lessons"], 1)
        self.assertEqual(response.data["completed_lessons"], 1)
        self.assertEqual(response.data["progress_percentage"], 100.0)
        self.assertTrue(response.data["is_completed"])
