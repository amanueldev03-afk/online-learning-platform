from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    LoginSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    InstructorProfileSerializer,
    LearnerProfileSerializer,
)
from .services import create_user, generate_tokens


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