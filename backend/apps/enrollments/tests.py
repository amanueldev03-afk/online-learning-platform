from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.enrollments.models import Enrollment
from apps.courses.models import Course, CourseSection, Lesson
from apps.categories.models import Category
from apps.accounts.models import User

User = get_user_model()


class EnrollmentModelTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
            role=User.Role.INSTRUCTOR
        )
        self.learner = User.objects.create_user(
            email="learner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Learner",
            role=User.Role.LEARNER
        )
        self.course = Course.objects.create(
            title="Test Course",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.PUBLISHED,
            price=99.99
        )

    def test_enrollment_creation(self):
        enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        self.assertEqual(enrollment.learner, self.learner)
        self.assertEqual(enrollment.course, self.course)
        self.assertEqual(enrollment.status, Enrollment.Status.ACTIVE)

    def test_unique_enrollment(self):
        Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        with self.assertRaises(Exception):
            Enrollment.objects.create(
                learner=self.learner,
                course=self.course,
                status=Enrollment.Status.ACTIVE
            )

    def test_enrollment_str(self):
        enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        self.assertEqual(str(enrollment), f"{self.learner.email} - {self.course.title}")


class EnrollmentAccessTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
            role=User.Role.INSTRUCTOR
        )
        self.learner = User.objects.create_user(
            email="learner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Learner",
            role=User.Role.LEARNER
        )
        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="adminpass123"
        )
        self.course = Course.objects.create(
            title="Test Course",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.PUBLISHED,
            price=99.99
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Test Section",
            order=1
        )
        self.free_lesson = Lesson.objects.create(
            section=self.section,
            title="Free Lesson",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video",
            duration_minutes=10,
            order=1,
            is_free_preview=True
        )
        self.private_lesson = Lesson.objects.create(
            section=self.section,
            title="Private Lesson",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video",
            duration_minutes=10,
            order=2,
            is_free_preview=False
        )

    def test_free_preview_access(self):
        from apps.enrollments.access import can_access_lesson
        result = can_access_lesson(
            user=None,
            lesson=self.free_lesson
        )
        self.assertTrue(result)

    def test_private_lesson_without_enrollment(self):
        from apps.enrollments.access import can_access_lesson
        result = can_access_lesson(
            user=self.learner,
            lesson=self.private_lesson
        )
        self.assertFalse(result)

    def test_private_lesson_with_active_enrollment(self):
        from apps.enrollments.access import can_access_lesson
        Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        result = can_access_lesson(
            user=self.learner,
            lesson=self.private_lesson
        )
        self.assertTrue(result)

    def test_private_lesson_with_completed_enrollment(self):
        from apps.enrollments.access import can_access_lesson
        enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.completed_at = timezone.now()
        enrollment.save()
        result = can_access_lesson(
            user=self.learner,
            lesson=self.private_lesson
        )
        self.assertTrue(result)

    def test_private_lesson_with_cancelled_enrollment(self):
        from apps.enrollments.access import can_access_lesson
        enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        enrollment.status = Enrollment.Status.CANCELLED
        enrollment.save()
        result = can_access_lesson(
            user=self.learner,
            lesson=self.private_lesson
        )
        self.assertFalse(result)

    def test_admin_access_to_private_lesson(self):
        from apps.enrollments.access import can_access_lesson
        result = can_access_lesson(
            user=self.admin,
            lesson=self.private_lesson
        )
        self.assertTrue(result)

    def test_instructor_access_to_own_course_lesson(self):
        from apps.enrollments.access import can_access_lesson
        result = can_access_lesson(
            user=self.instructor,
            lesson=self.private_lesson
        )
        self.assertTrue(result)


class EnrollmentAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Instructor",
            role=User.Role.INSTRUCTOR
        )
        
        self.learner = User.objects.create_user(
            email="learner@test.com",
            password="testpass123",
            first_name="Test",
            last_name="Learner",
            role=User.Role.LEARNER
        )
        
        self.course = Course.objects.create(
            title="Test Course",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.PUBLISHED,
            price=99.99
        )

    def test_create_enrollment_learner_success(self):
        self.client.force_authenticate(user=self.learner)
        data = {
            "course": self.course.id
        }
        response = self.client.post('/api/enrollments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Enrollment.objects.filter(
            learner=self.learner,
            course=self.course
        ).exists())

    def test_create_enrollment_instructor_forbidden(self):
        self.client.force_authenticate(user=self.instructor)
        data = {
            "course": self.course.id
        }
        response = self.client.post('/api/enrollments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_enrollment_unauthenticated_forbidden(self):
        data = {
            "course": self.course.id
        }
        response = self.client.post('/api/enrollments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_enrollment_draft_course_forbidden(self):
        draft_course = Course.objects.create(
            title="Draft Course",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.DRAFT
        )
        self.client.force_authenticate(user=self.learner)
        data = {
            "course": draft_course.id
        }
        response = self.client.post('/api/enrollments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_enrollment_forbidden(self):
        Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        self.client.force_authenticate(user=self.learner)
        data = {
            "course": self.course.id
        }
        response = self.client.post('/api/enrollments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reactivate_cancelled_enrollment(self):
        enrollment = Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.CANCELLED
        )
        self.client.force_authenticate(user=self.learner)
        data = {
            "course": self.course.id
        }
        response = self.client.post('/api/enrollments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, Enrollment.Status.ACTIVE)


class MyEnrollmentsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR
        )
        
        self.learner = User.objects.create_user(
            email="learner@test.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        self.course1 = Course.objects.create(
            title="Course 1",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.course2 = Course.objects.create(
            title="Course 2",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        Enrollment.objects.create(
            learner=self.learner,
            course=self.course1,
            status=Enrollment.Status.ACTIVE
        )
        
        Enrollment.objects.create(
            learner=self.learner,
            course=self.course2,
            status=Enrollment.Status.COMPLETED
        )

    def test_list_my_enrollments_learner_success(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.get('/api/enrollments/my/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that we get at least the 2 enrollments we created
        self.assertGreaterEqual(len(response.data), 2)

    def test_list_my_enrollments_instructor_empty(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get('/api/enrollments/my/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_my_enrollments_unauthenticated_forbidden(self):
        response = self.client.get('/api/enrollments/my/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LessonDetailViewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        self.instructor = User.objects.create_user(
            email="instructor@test.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR
        )
        
        self.learner = User.objects.create_user(
            email="learner@test.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        
        self.course = Course.objects.create(
            title="Test Course",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Test Section",
            order=1
        )
        
        self.free_lesson = Lesson.objects.create(
            section=self.section,
            title="Free Lesson",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video",
            duration_minutes=10,
            order=1,
            is_free_preview=True
        )
        
        self.private_lesson = Lesson.objects.create(
            section=self.section,
            title="Private Lesson",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video",
            duration_minutes=10,
            order=2,
            is_free_preview=False
        )

    def test_access_free_lesson_unauthenticated(self):
        response = self.client.get(f'/api/enrollments/lessons/{self.free_lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_private_lesson_unauthenticated_forbidden(self):
        response = self.client.get(f'/api/enrollments/lessons/{self.private_lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_private_lesson_with_enrollment_allowed(self):
        Enrollment.objects.create(
            learner=self.learner,
            course=self.course,
            status=Enrollment.Status.ACTIVE
        )
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(f'/api/enrollments/lessons/{self.private_lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_private_lesson_without_enrollment_forbidden(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(f'/api/enrollments/lessons/{self.private_lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_lesson_from_draft_course_not_found(self):
        draft_course = Course.objects.create(
            title="Draft Course",
            instructor=self.instructor,
            category=self.category,
            status=Course.Status.DRAFT
        )
        draft_section = CourseSection.objects.create(
            course=draft_course,
            title="Draft Section",
            order=1
        )
        draft_lesson = Lesson.objects.create(
            section=draft_section,
            title="Draft Lesson",
            content_type=Lesson.ContentType.VIDEO,
            video_url="https://example.com/video",
            duration_minutes=10,
            order=1
        )
        response = self.client.get(f'/api/enrollments/lessons/{draft_lesson.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
