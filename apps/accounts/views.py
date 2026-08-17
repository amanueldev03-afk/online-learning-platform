from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError, APIException


from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

from .models import User
from .serializers import (
    AdminLoginSerializer,
    LoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    InstructorProfileSerializer,
    LearnerProfileSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    GoogleLoginSerializer,
)
from .services import create_user, generate_tokens, create_verification_token, create_password_reset_token

from .email_services import (
    send_verification_email,
    send_password_reset_email,
)

from .google_services import (
    GoogleAuthenticationError,
    verify_google_credential,
)

from .oauth_services import (
    get_or_create_google_user,
    link_google_account,
    create_google_jwt_tokens,
)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="register",
        description="Register a new user account",
        request=UserRegistrationSerializer,
        responses={201: UserSerializer}
    )
    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(
                data=request.data
            )

            serializer.is_valid(raise_exception=True)

            user = create_user(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                first_name=serializer.validated_data["first_name"],
                last_name=serializer.validated_data["last_name"],
                role=serializer.validated_data["role"],
            )

            return Response(
                {
                    "message": "Account created successfully.",
                    "user": UserSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            logger.error(f"Registration validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return Response(
                {"detail": "An error occurred during registration."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="login",
        description="Login with email and password",
        request=LoginSerializer,
        responses={200: OpenApiResponse(description="Login successful")}
    )
    def post(self, request):
        try:
            serializer = LoginSerializer(
                data=request.data,
                context={"request": request},
            )

            serializer.is_valid(raise_exception=True)

            user = serializer.validated_data["user"]

            tokens = generate_tokens(user)

            return Response(
                {
                    "message": "Login successful.",
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Login validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Login error: {e}")
            return Response(
                {"detail": "An error occurred during login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="me",
        description="Get current user information",
        responses={200: UserSerializer}
    )
    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="logout",
        description="Logout and blacklist refresh token",
        request={"type": "object", "properties": {"refresh": {"type": "string"}}},
        responses={200: None}
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {
                        "detail": "Refresh token is required."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                token = RefreshToken(refresh_token)
                token.blacklist()

            except Exception as e:
                logger.error(f"Token blacklist error: {e}")
                return Response(
                    {
                        "detail": "Invalid refresh token."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                {
                    "message": "Logout successful."
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return Response(
                {"detail": "An error occurred during logout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        operation_id="my_profile",
        description="Get current user's profile",
        responses={200: OpenApiResponse(description="Profile retrieved successfully")}
    )
    def get(self, request):
        try:
            user = request.user

            if user.role == User.Role.LEARNER:
                return Response(
                    {
                        "role": user.role,
                        "profile": LearnerProfileSerializer(
                            user.learner_profile
                        ).data,
                    }
                )

            if user.role == User.Role.INSTRUCTOR:
                return Response(
                    {
                        "role": user.role,
                        "profile": InstructorProfileSerializer(
                            user.instructor_profile
                        ).data,
                    }
                )

            return Response(
                {
                    "role": user.role,
                    "profile": None,
                }
            )
        except Exception as e:
            logger.error(f"Profile retrieval error: {e}")
            return Response(
                {"detail": "An error occurred while retrieving profile."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        operation_id="update_my_profile",
        description="Update current user's profile",
        request=LearnerProfileSerializer,
        responses={200: OpenApiResponse(description="Profile updated successfully")}
    )
    def patch(self, request):
        try:
            user = request.user

            if user.role == User.Role.LEARNER:
                profile = user.learner_profile

                serializer = LearnerProfileSerializer(
                    profile,
                    data=request.data,
                    partial=True,
                )

            elif user.role == User.Role.INSTRUCTOR:
                profile = user.instructor_profile

                serializer = InstructorProfileSerializer(
                    profile,
                    data=request.data,
                    partial=True,
                )

            else:
                return Response(
                    {
                        "detail": "Administrator profile is managed separately."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Profile update validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Profile update error: {e}")
            return Response(
                {"detail": "An error occurred while updating profile."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="verify_email",
        description="Verify email address with token",
        request=EmailVerificationSerializer,
        responses={200: OpenApiResponse(description="Email verified successfully")}
    )
    def post(self, request):
        try:
            serializer = EmailVerificationSerializer(
                data=request.data
            )

            serializer.is_valid(
                raise_exception=True
            )

            verification = (
                serializer.validated_data[
                    "verification"
                ]
            )

            user = verification.user

            user.email_verified = True

            user.save(
                update_fields=["email_verified"]
            )

            verification.used_at = timezone.now()

            verification.save(
                update_fields=["used_at"]
            )

            return Response(
                {
                    "message": (
                        "Email verified successfully."
                    ),
                    "email_verified": True,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Email verification validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            return Response(
                {"detail": "An error occurred during email verification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="resend_verification",
        description="Resend email verification",
        request=ResendVerificationSerializer,
        responses={200: OpenApiResponse(description="Verification email sent")}
    )
    def post(self, request):
        try:
            serializer = ResendVerificationSerializer(
                data=request.data
            )

            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data["email"]

            try:
                user = User.objects.get(email=email)

            except User.DoesNotExist:
                return Response(
                    {
                        "message": (
                            "If an account exists with this email, "
                            "a verification email has been sent."
                        )
                    },
                    status=status.HTTP_200_OK,
                )

            if not user.email_verified:
                raw_token, _ = create_verification_token(user)
                send_verification_email(user, raw_token)

            return Response(
                {
                    "message": (
                        "If an account exists with this email, "
                        "a verification email has been sent."
                    )
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Resend verification validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Resend verification error: {e}")
            return Response(
                {"detail": "An error occurred while resending verification."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="password_reset_request",
        description="Request password reset email",
        request=PasswordResetRequestSerializer,
        responses={200: OpenApiResponse(description="Password reset email sent")}
    )
    def post(self, request):
        try:
            serializer = PasswordResetRequestSerializer(
                data=request.data
            )

            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data["email"]

            user = User.objects.filter(
                email=email,
                is_active=True,
            ).first()

            if user:
                raw_token, _ = create_password_reset_token(user)
                send_password_reset_email(user, raw_token)

            return Response(
                {
                    "message": (
                        "If an account exists with this email, "
                        "a password reset link has been sent."
                    )
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Password reset request validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Password reset request error: {e}")
            return Response(
                {"detail": "An error occurred while requesting password reset."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="password_reset_confirm",
        description="Confirm password reset with token",
        request=PasswordResetConfirmSerializer,
        responses={200: OpenApiResponse(description="Password reset successful")}
    )
    def post(self, request):
        try:
            serializer = PasswordResetConfirmSerializer(
                data=request.data
            )

            serializer.is_valid(raise_exception=True)

            user = serializer.validated_data["user"]
            reset_token = serializer.validated_data["reset_token"]

            user.set_password(
                serializer.validated_data["password"]
            )

            user.save(
                update_fields=["password"]
            )

            reset_token.used_at = timezone.now()
            reset_token.save(
                update_fields=["used_at"]
            )

            return Response(
                {
                    "message": (
                        "Password reset successfully."
                    )
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Password reset confirm validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Password reset confirm error: {e}")
            return Response(
                {"detail": "An error occurred during password reset."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="google_login",
        description="Login with Google OAuth",
        request=GoogleLoginSerializer,
        responses={200: OpenApiResponse(description="Google login successful")}
    )
    def post(self, request):
        try:
            serializer = GoogleLoginSerializer(
                data=request.data
            )

            serializer.is_valid(
                raise_exception=True
            )

            credential = serializer.validated_data[
                "credential"
            ]

            role = serializer.validated_data.get(
                "role"
            )

            # -----------------------------------
            # 1. Verify Google identity
            # -----------------------------------

            try:

                google_user = verify_google_credential(
                    credential
                )

            except GoogleAuthenticationError as exc:

                return Response(
                    {
                        "detail": str(exc)
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # -----------------------------------
            # 2. Create/find application user
            # -----------------------------------

            try:

                user, created = (
                    get_or_create_google_user(
                        email=google_user["email"],
                        first_name=google_user["first_name"],
                        last_name=google_user["last_name"],
                        google_id=google_user["google_id"],
                        role=role,
                    )
                )

            except ValueError as exc:

                return Response(
                    {
                        "detail": str(exc)
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # -----------------------------------
            # 3. Link Google account
            # -----------------------------------

            try:

                link_google_account(
                    user=user,
                    google_id=google_user["google_id"],
                )

            except ValueError as exc:

                return Response(
                    {
                        "detail": str(exc)
                    },
                    status=status.HTTP_409_CONFLICT,
                )

            # -----------------------------------
            # 4. Generate application JWT
            # -----------------------------------

            tokens = create_google_jwt_tokens(
                user
            )

            return Response(
                {
                    "message": (
                        "Google login successful."
                    ),
                    "is_new_user": created,
                    "user": UserSerializer(
                        user
                    ).data,
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Google login validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Google login error: {e}")
            return Response(
                {"detail": "An error occurred during Google login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="admin_login",
        description="Admin login with email and password (no email verification required)",
        request=AdminLoginSerializer,
        responses={200: OpenApiResponse(description="Admin login successful")}
    )
    def post(self, request):
        try:
            serializer = AdminLoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            email = serializer.validated_data["email"]
            password = serializer.validated_data["password"]

            from django.contrib.auth import authenticate

            user = authenticate(request, username=email, password=password)

            if not user:
                return Response(
                    {"detail": "Invalid email or password."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not (user.is_staff or user.is_superuser):
                return Response(
                    {"detail": "Access denied. Admin access only."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not user.is_active:
                return Response(
                    {"detail": "Account is inactive."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            tokens = generate_tokens(user)

            return Response(
                {
                    "message": "Admin login successful.",
                    "user": UserSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            logger.error(f"Admin login validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Admin login error: {e}")
            return Response(
                {"detail": "An error occurred during admin login."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )