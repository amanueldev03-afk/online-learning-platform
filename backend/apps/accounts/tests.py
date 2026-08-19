from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
import json

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            role=User.Role.LEARNER
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
        self.assertEqual(self.user.role, User.Role.LEARNER)
        self.assertTrue(self.user.check_password("testpass123"))

    def test_user_str(self):
        self.assertEqual(str(self.user), "test@example.com")

    def test_user_roles(self):
        instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            role=User.Role.INSTRUCTOR
        )
        admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.assertEqual(instructor.role, User.Role.INSTRUCTOR)
        self.assertEqual(admin.role, User.Role.ADMIN)


class UserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration(self):
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "TestPass123",
            "password_confirm": "TestPass123",
            "role": "LEARNER"
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_user_registration_password_mismatch(self):
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "TestPass123",
            "password_confirm": "DifferentPass123",
            "role": "LEARNER"
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_duplicate_email(self):
        User.objects.create_user(
            email="existing@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        data = {
            "email": "existing@example.com",
            "first_name": "New",
            "last_name": "User",
            "password": "TestPass123",
            "password_confirm": "TestPass123",
            "role": "LEARNER"
        }
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            role=User.Role.LEARNER
        )

    def test_user_login_success(self):
        self.user.email_verified = True
        self.user.save()
        data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_user_login_invalid_credentials(self):
        data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login_unverified_email(self):
        user = User.objects.create_user(
            email="unverified@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        user.email_verified = False
        user.save()
        
        data = {
            "email": "unverified@example.com",
            "password": "testpass123"
        }
        response = self.client.post('/api/auth/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.learner = User.objects.create_user(
            email="learner@example.com",
            password="testpass123",
            first_name="Learner",
            last_name="User",
            role=User.Role.LEARNER
        )
        self.instructor = User.objects.create_user(
            email="instructor@example.com",
            password="testpass123",
            first_name="Instructor",
            last_name="User",
            role=User.Role.INSTRUCTOR
        )

    def test_get_learner_profile(self):
        from apps.accounts.models import LearnerProfile
        LearnerProfile.objects.create(user=self.learner)
        self.client.force_authenticate(user=self.learner)
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'LEARNER')

    def test_get_instructor_profile(self):
        from apps.accounts.models import InstructorProfile
        InstructorProfile.objects.create(user=self.instructor)
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'INSTRUCTOR')

    def test_update_profile_unauthenticated(self):
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmailVerificationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Role.LEARNER
        )
        from apps.accounts.services import create_verification_token
        self.raw_token, self.token = create_verification_token(self.user)

    def test_email_verification(self):
        data = {
            "token": self.raw_token
        }
        response = self.client.post('/api/auth/verify-email/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_email_verification_invalid_token(self):
        data = {
            "token": "invalid_token"
        }
        response = self.client.post('/api/auth/verify-email/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="oldpass123",
            role=User.Role.LEARNER
        )

    def test_password_reset_request(self):
        data = {
            "email": "test@example.com"
        }
        response = self.client.post('/api/auth/forgot-password/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_nonexistent_email(self):
        data = {
            "email": "nonexistent@example.com"
        }
        response = self.client.post('/api/auth/forgot-password/', data, format='json')
        # Should still return 200 for security (don't reveal email existence)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AdminLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )

    def test_admin_login(self):
        data = {
            "email": "admin@example.com",
            "password": "adminpass123"
        }
        response = self.client.post('/api/auth/admin/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['tokens'])

    def test_admin_login_with_regular_user(self):
        regular_user = User.objects.create_user(
            email="user@example.com",
            password="testpass123"
        )
        data = {
            "email": "user@example.com",
            "password": "testpass123"
        }
        response = self.client.post('/api/auth/admin/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

