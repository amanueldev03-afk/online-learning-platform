from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from apps.accounts.models import User, LearnerProfile, InstructorProfile

User = get_user_model()


class RegisterViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'

    def test_register_learner_success(self):
        data = {
            'email': 'learner@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'role': 'LEARNER'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['email'], 'learner@example.com')
        self.assertEqual(response.data['user']['role'], 'LEARNER')
        self.assertTrue(User.objects.filter(email='learner@example.com').exists())
        self.assertTrue(LearnerProfile.objects.filter(user__email='learner@example.com').exists())

    def test_register_instructor_success(self):
        data = {
            'email': 'instructor@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'role': 'INSTRUCTOR'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['role'], 'INSTRUCTOR')
        self.assertTrue(InstructorProfile.objects.filter(user__email='instructor@example.com').exists())

    def test_register_password_mismatch(self):
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'DifferentPass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'LEARNER'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_admin_role_rejected(self):
        data = {
            'email': 'admin@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'ADMIN'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(
            email='existing@example.com',
            password='TestPass123!',
            first_name='Existing',
            last_name='User',
            role='LEARNER'
        )
        data = {
            'email': 'existing@example.com',
            'password': 'TestPass123!',
            'password_confirm': 'TestPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'LEARNER'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/auth/login/'
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            role='LEARNER'
        )
        self.user.email_verified = True
        self.user.save()

    def test_login_success(self):
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])

    def test_login_invalid_credentials(self):
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_unverified_email(self):
        self.user.email_verified = False
        self.user.save()
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_account(self):
        self.user.is_active = False
        self.user.save()
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.logout_url = '/api/auth/logout/'
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            role='LEARNER'
        )
        self.user.email_verified = True
        self.user.save()

    def test_logout_success(self):
        # First login to get tokens
        login_response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'TestPass123!'
        })
        refresh_token = login_response.data['tokens']['refresh']
        
        # Then logout
        response = self.client.post(self.logout_url, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_missing_token(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.logout_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_invalid_token(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.logout_url, {'refresh': 'invalid_token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MeViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.me_url = '/api/auth/me/'
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            role='LEARNER'
        )

    def test_get_current_user_authenticated(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_get_current_user_unauthenticated(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MyProfileViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.profile_url = '/api/auth/my-profile/'
        self.learner = User.objects.create_user(
            email='learner@example.com',
            password='TestPass123!',
            first_name='John',
            last_name='Doe',
            role='LEARNER'
        )
        self.instructor = User.objects.create_user(
            email='instructor@example.com',
            password='TestPass123!',
            first_name='Jane',
            last_name='Smith',
            role='INSTRUCTOR'
        )

    def test_get_learner_profile(self):
        self.client.force_authenticate(user=self.learner)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'LEARNER')

    def test_get_instructor_profile(self):
        self.client.force_authenticate(user=self.instructor)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['role'], 'INSTRUCTOR')

    def test_update_learner_profile(self):
        self.client.force_authenticate(user=self.learner)
        data = {
            'bio': 'New bio for learner',
            'country': 'USA'
        }
        response = self.client.patch(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.learner.learner_profile.refresh_from_db()
        self.assertEqual(self.learner.learner_profile.bio, 'New bio for learner')

    def test_update_instructor_profile(self):
        self.client.force_authenticate(user=self.instructor)
        data = {
            'specialization': 'Python Programming',
            'experience_years': 5
        }
        response = self.client.patch(self.profile_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.instructor.instructor_profile.refresh_from_db()
        self.assertEqual(self.instructor.instructor_profile.specialization, 'Python Programming')


class VerifyEmailViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.verify_url = '/api/auth/verify-email/'
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            role='LEARNER'
        )

    def test_verify_email_success(self):
        from apps.accounts.services import create_verification_token
        raw_token, verification_token = create_verification_token(self.user)
        
        response = self.client.post(self.verify_url, {'token': raw_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_verify_email_invalid_token(self):
        response = self.client.post(self.verify_url, {'token': 'invalid_token'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_expired_token(self):
        from apps.accounts.services import create_verification_token
        from django.utils import timezone
        from datetime import timedelta
        
        raw_token, verification_token = create_verification_token(self.user)
        verification_token.expires_at = timezone.now() - timedelta(hours=25)
        verification_token.save()
        
        response = self.client.post(self.verify_url, {'token': raw_token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.request_url = '/api/auth/password-reset-request/'
        self.confirm_url = '/api/auth/password-reset-confirm/'
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='User',
            role='LEARNER'
        )

    def test_password_reset_request_success(self):
        response = self.client.post(self.request_url, {'email': 'test@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_request_nonexistent_email(self):
        response = self.client.post(self.request_url, {'email': 'nonexistent@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Security: don't reveal email existence

    def test_password_reset_confirm_success(self):
        from apps.accounts.services import create_password_reset_token
        raw_token, reset_token = create_password_reset_token(self.user)
        
        data = {
            'token': raw_token,
            'password': 'NewPass123!',
            'password_confirm': 'NewPass123!'
        }
        response = self.client.post(self.confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_password_reset_confirm_password_mismatch(self):
        from apps.accounts.services import create_password_reset_token
        raw_token, reset_token = create_password_reset_token(self.user)
        
        data = {
            'token': raw_token,
            'password': 'NewPass123!',
            'password_confirm': 'DifferentPass123!'
        }
        response = self.client.post(self.confirm_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
