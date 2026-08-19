from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.categories.models import Category
from apps.accounts.models import User

User = get_user_model()


class CategoryListCreateViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.list_url = '/api/categories/'
        
        # Create test categories
        self.category1 = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses',
            is_active=True
        )
        self.category2 = Category.objects.create(
            name='Design',
            slug='design',
            description='Design courses',
            is_active=True
        )
        self.inactive_category = Category.objects.create(
            name='Inactive',
            slug='inactive',
            description='Inactive category',
            is_active=False
        )

    def test_list_categories_public(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that we get at least the 2 active categories we created
        self.assertGreaterEqual(len(response.data), 2)

    def test_list_categories_with_pagination(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

    def test_create_category_admin_success(self):
        admin_user = User.objects.create_user(
            email='admin@example.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        admin_user.is_staff = True
        admin_user.save()
        
        self.client.force_authenticate(user=admin_user)
        data = {
            'name': 'New Category',
            'slug': 'new-category',
            'description': 'A new category'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name='New Category').exists())

    def test_create_category_non_admin_forbidden(self):
        learner = User.objects.create_user(
            email='learner@example.com',
            password='TestPass123!',
            first_name='Learner',
            last_name='User',
            role='LEARNER'
        )
        
        self.client.force_authenticate(user=learner)
        data = {
            'name': 'New Category',
            'slug': 'new-category',
            'description': 'A new category'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_category_unauthenticated_forbidden(self):
        data = {
            'name': 'New Category',
            'slug': 'new-category',
            'description': 'A new category'
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CategoryDetailViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses',
            is_active=True
        )
        self.detail_url = f'/api/categories/{self.category.id}/'
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='TestPass123!',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        self.admin_user.is_staff = True
        self.admin_user.save()
        
        self.learner = User.objects.create_user(
            email='learner@example.com',
            password='TestPass123!',
            first_name='Learner',
            last_name='User',
            role='LEARNER'
        )

    def test_get_category_authenticated(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Programming')

    def test_get_category_unauthenticated(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_category_not_found(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.get('/api/categories/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_category_admin_success(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Updated Programming',
            'description': 'Updated description'
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, 'Updated Programming')

    def test_update_category_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.learner)
        data = {
            'name': 'Updated Programming',
            'description': 'Updated description'
        }
        response = self.client.patch(self.detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_category_admin_success(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())

    def test_delete_category_non_admin_forbidden(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_category_with_courses_forbidden(self):
        # Create a course that uses this category
        from apps.courses.models import Course
        instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='Instructor',
            last_name='User',
            role='INSTRUCTOR'
        )
        
        Course.objects.create(
            instructor=instructor,
            title='Test Course',
            slug='test-course',
            short_description='Test',
            description='Test description',
            category=self.category
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CategoryModelTestCase(TestCase):
    def test_category_slug_auto_generation(self):
        category = Category.objects.create(
            name='Web Development',
            description='Web dev courses'
        )
        self.assertEqual(category.slug, 'web-development')

    def test_category_parent_child_relationship(self):
        parent = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Tech courses'
        )
        child = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses',
            parent=parent
        )
        self.assertEqual(child.parent, parent)
        self.assertEqual(parent.children.count(), 1)

    def test_category_str_representation(self):
        category = Category.objects.create(
            name='Design',
            slug='design',
            description='Design courses'
        )
        self.assertEqual(str(category), 'Design')

    def test_category_ordering(self):
        category1 = Category.objects.create(
            name='First',
            slug='first',
            description='First category',
            display_order=2
        )
        category2 = Category.objects.create(
            name='Second',
            slug='second',
            description='Second category',
            display_order=1
        )
        
        categories = list(Category.objects.all())
        # Should be ordered by display_order
        self.assertEqual(categories[0].name, 'Second')
        self.assertEqual(categories[1].name, 'First')


class CategorySerializerTestCase(TestCase):
    def setUp(self):
        self.parent = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Tech courses'
        )
        self.category = Category.objects.create(
            name='Programming',
            slug='programming',
            description='Programming courses',
            parent=self.parent
        )

    def test_category_serializer_includes_parent(self):
        from apps.categories.serializers import CategorySerializer
        serializer = CategorySerializer(self.category)
        data = serializer.data
        self.assertIn('parent', data)
        self.assertEqual(data['parent'], self.parent.id)

    def test_category_serializer_validation(self):
        from apps.categories.serializers import CategorySerializer
        # Test duplicate name
        data = {
            'name': 'Programming',
            'slug': 'different-slug',
            'description': 'Another programming category'
        }
        serializer = CategorySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
