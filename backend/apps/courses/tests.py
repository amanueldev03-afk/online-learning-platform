from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.courses.models import Course, CourseSection, Lesson
from apps.categories.models import Category
from apps.accounts.models import User

User = get_user_model()


class CourseListCreateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/courses/'
        
        # Create test users
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        self.learner = User.objects.create_user(
            email='learner@example.com',
            password='TestPass123!',
            first_name='Jane',
            last_name='Smith',
            role='LEARNER'
        )
        
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        self.admin.is_staff = True
        self.admin.save()
        
        # Create test category
        self.category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        # Create published course
        self.published_course = Course.objects.create(
            instructor=self.instructor,
            title='Python Basics',
            slug='python-basics',
            short_description='Learn Python',
            description='Comprehensive Python course',
            category=self.category,
            status=Course.Status.PUBLISHED,
            is_free=True
        )
        
        # Create draft course
        self.draft_course = Course.objects.create(
            instructor=self.instructor,
            title='Advanced Python',
            slug='advanced-python',
            short_description='Advanced Python',
            description='Advanced Python concepts',
            category=self.category,
            status=Course.Status.DRAFT
        )

    def test_list_courses_public(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)  # Only published courses

    def test_list_courses_with_pagination(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_list_courses_with_filters(self):
        response = self.client.get(f'{self.list_url}?category={self.category.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_courses_with_search(self):
        response = self.client.get(f'{self.list_url}?search=Python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_course_instructor_success(self):
        self.client.force_authenticate(user=self.instructor)
        data = {
            'title': 'New Course',
            'slug': 'new-course',
            'short_description': 'New course description',
            'description': 'Full course description',
            'category': self.category.id,
            'level': 'BEGINNER',
            'is_free': True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(title='New Course').exists())

    def test_create_course_learner_forbidden(self):
        self.client.force_authenticate(user=self.learner)
        data = {
            'title': 'New Course',
            'slug': 'new-course',
            'short_description': 'New course description',
            'description': 'Full course description',
            'category': self.category.id,
            'level': 'BEGINNER',
            'is_free': True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_course_unauthenticated_forbidden(self):
        data = {
            'title': 'New Course',
            'slug': 'new-course',
            'short_description': 'New course description',
            'description': 'Full course description',
            'category': self.category.id,
            'level': 'BEGINNER',
            'is_free': True
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CourseDetailViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        self.other_instructor = User.objects.create_user(
            email='other@example.com',
            password='TestPass123!',
            first_name='Other',
            last_name='Instructor',
            role='INSTRUCTOR'
        )
        
        self.admin = User.objects.create_user(
            email='admin@example.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        self.admin.is_staff = True
        self.admin.save()
        
        self.category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title='Python Basics',
            slug='python-basics',
            short_description='Learn Python',
            description='Comprehensive Python course',
            category=self.category,
            status=Course.Status.PUBLISHED,
            is_free=True
        )
        
        self.detail_url = f'/api/courses/{self.course.id}/'

    def test_get_published_course_public(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Python Basics')

    def test_get_draft_course_unauthenticated_forbidden(self):
        draft_course = Course.objects.create(
            instructor=self.instructor,
            title='Draft Course',
            slug='draft-course',
            short_description='Draft',
            description='Draft description',
            category=self.category,
            status=Course.Status.DRAFT
        )
        response = self.client.get(f'/api/courses/{draft_course.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_draft_course_instructor_owner_allowed(self):
        draft_course = Course.objects.create(
            instructor=self.instructor,
            title='Draft Course',
            slug='draft-course',
            short_description='Draft',
            description='Draft description',
            category=self.category,
            status=Course.Status.DRAFT
        )
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(f'/api/courses/{draft_course.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_course_instructor_owner_success(self):
        self.client.force_authenticate(user=self.instructor)
        data = {
            'title': 'Updated Python Basics',
            'short_description': 'Updated description'
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.title, 'Updated Python Basics')

    def test_update_course_other_instructor_forbidden(self):
        self.client.force_authenticate(user=self.other_instructor)
        data = {
            'title': 'Updated Python Basics',
            'short_description': 'Updated description'
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_course_admin_success(self):
        self.client.force_authenticate(user=self.admin)
        data = {
            'title': 'Admin Updated Course',
            'short_description': 'Admin update'
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_course_instructor_owner_success(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_delete_course_other_instructor_forbidden(self):
        self.client.force_authenticate(user=self.other_instructor)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CoursePublishViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        self.other_instructor = User.objects.create_user(
            email='other@example.com',
            password='TestPass123!',
            first_name='Other',
            last_name='Instructor',
            role='INSTRUCTOR'
        )
        
        self.category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title='Python Basics',
            slug='python-basics',
            short_description='Learn Python',
            description='Comprehensive Python course',
            category=self.category,
            status=Course.Status.DRAFT
        )
        
        self.publish_url = f'/api/courses/{self.course.id}/publish/'

    def test_publish_course_instructor_owner_success(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.publish_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course.refresh_from_db()
        self.assertEqual(self.course.status, Course.Status.PUBLISHED)

    def test_publish_course_other_instructor_forbidden(self):
        self.client.force_authenticate(user=self.other_instructor)
        response = self.client.post(self.publish_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_publish_already_published_course(self):
        self.course.status = Course.Status.PUBLISHED
        self.course.save()
        self.client.force_authenticate(user=self.instructor)
        response = self.client.post(self.publish_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CourseSectionListCreateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        self.category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title='Python Basics',
            slug='python-basics',
            short_description='Learn Python',
            description='Comprehensive Python course',
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.sections_url = f'/api/courses/{self.course.id}/sections/'

    def test_list_sections_authenticated(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.sections_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_section_instructor_owner_success(self):
        self.client.force_authenticate(user=self.instructor)
        data = {
            'title': 'Introduction',
            'description': 'Course introduction',
            'order': 1
        }
        response = self.client.post(self.sections_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CourseSection.objects.filter(title='Introduction').exists())

    def test_create_section_unauthenticated_forbidden(self):
        data = {
            'title': 'Introduction',
            'description': 'Course introduction',
            'order': 1
        }
        response = self.client.post(self.sections_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LessonListCreateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        self.category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        self.course = Course.objects.create(
            instructor=self.instructor,
            title='Python Basics',
            slug='python-basics',
            short_description='Learn Python',
            description='Comprehensive Python course',
            category=self.category,
            status=Course.Status.PUBLISHED
        )
        
        self.section = CourseSection.objects.create(
            course=self.course,
            title='Introduction',
            description='Course introduction',
            order=1
        )
        
        self.lessons_url = f'/api/courses/sections/{self.section.id}/lessons/'

    def test_list_lessons_authenticated(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.lessons_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_lesson_instructor_owner_success(self):
        self.client.force_authenticate(user=self.instructor)
        data = {
            'title': 'First Lesson',
            'description': 'Lesson description',
            'content_type': 'VIDEO',
            'video_url': 'https://example.com/video.mp4',
            'duration_minutes': 10,
            'order': 1
        }
        response = self.client.post(self.lessons_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lesson.objects.filter(title='First Lesson').exists())

    def test_create_lesson_unauthenticated_forbidden(self):
        data = {
            'title': 'First Lesson',
            'description': 'Lesson description',
            'content_type': 'VIDEO',
            'video_url': 'https://example.com/video.mp4',
            'duration_minutes': 10,
            'order': 1
        }
        response = self.client.post(self.lessons_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CourseModelTestCase(TestCase):
    def test_course_slug_auto_generation(self):
        instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        course = Course.objects.create(
            instructor=instructor,
            title='Python Programming Course',
            short_description='Learn Python',
            description='Full description'
        )
        self.assertEqual(course.slug, 'python-programming-course')

    def test_course_str_representation(self):
        instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        course = Course.objects.create(
            instructor=instructor,
            title='Python Basics',
            short_description='Learn Python',
            description='Full description'
        )
        self.assertEqual(str(course), 'Python Basics')

    def test_course_section_ordering(self):
        instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        course = Course.objects.create(
            instructor=instructor,
            title='Python Basics',
            short_description='Learn Python',
            description='Full description',
            category=category
        )
        
        section1 = CourseSection.objects.create(
            course=course,
            title='Section 2',
            order=2
        )
        
        section2 = CourseSection.objects.create(
            course=course,
            title='Section 1',
            order=1
        )
        
        sections = list(course.sections.all())
        self.assertEqual(sections[0].title, 'Section 1')
        self.assertEqual(sections[1].title, 'Section 2')


class CourseSerializerTestCase(TestCase):
    def test_course_price_validation_free_course(self):
        from apps.courses.serializers import CourseSerializer
        instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        # Free course with non-zero price should fail
        data = {
            'instructor': instructor.id,
            'title': 'Test Course',
            'slug': 'test-course',
            'short_description': 'Test',
            'description': 'Test description',
            'category': category.id,
            'is_free': True,
            'price': 10.00
        }
        serializer = CourseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)

    def test_course_price_validation_paid_course(self):
        from apps.courses.serializers import CourseSerializer
        instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='INSTRUCTOR'
        )
        
        category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses'
        )
        
        # Paid course with zero price should fail
        data = {
            'instructor': instructor.id,
            'title': 'Test Course',
            'slug': 'test-course',
            'short_description': 'Test',
            'description': 'Test description',
            'category': category.id,
            'is_free': False,
            'price': 0
        }
        serializer = CourseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('price', serializer.errors)
