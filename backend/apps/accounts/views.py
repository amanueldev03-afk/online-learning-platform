from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from django.utils import timezone

from .models import User
from .serializers import (
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

    def post(self, request):
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


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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

        except Exception:
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

class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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

    def patch(self, request):
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


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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



class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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



class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
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



class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

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