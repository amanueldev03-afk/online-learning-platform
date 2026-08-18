from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

from apps.accounts.models import User

from .models import Category
from .serializers import CategorySerializer


class CategoryListCreateView(ListCreateAPIView):

    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        if self.request.method == "POST":
            return [IsAuthenticated()]

        return [IsAuthenticated()]

    def get_queryset(self):
        return Category.objects.filter(
            is_active=True,
        ).select_related(
            "parent",
        )

    @extend_schema(
        operation_id="list_categories",
        description="List all active categories",
        responses={200: CategorySerializer(many=True)}
    )

    @extend_schema(
        operation_id="create_category",
        description="Create a new category (admin only)",
        request=CategorySerializer,
        responses={201: CategorySerializer}
    )
    def post(self, request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {
                    "detail": (
                        "Only administrators can "
                        "create categories."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().post(request, *args, **kwargs)



class CategoryDetailView(APIView):

    permission_classes = [
        IsAuthenticated,
    ]

    def get_object(self, pk):

        return Category.objects.filter(
            pk=pk,
        ).first()

    @extend_schema(
        operation_id="get_category",
        description="Get category details",
        responses={200: CategorySerializer}
    )
    def get(self, request, pk):

        category = self.get_object(pk)

        if not category:
            return Response(
                {
                    "detail": "Category not found."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CategorySerializer(category).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="update_category",
        description="Update category (admin only)",
        request=CategorySerializer,
        responses={200: CategorySerializer}
    )
    def patch(self, request, pk):
        try:
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {
                        "detail": (
                            "Only administrators can "
                            "update categories."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            category = self.get_object(pk)

            if not category:
                return Response(
                    {
                        "detail": "Category not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = CategorySerializer(
                category,
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
        except ValidationError as e:
            logger.error(f"Category update validation error: {e}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Category update error: {e}")
            return Response(
                {"detail": "An error occurred during category update."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        operation_id="delete_category",
        description="Delete category (admin only)",
        responses={204: OpenApiResponse(description="Category deleted successfully")}
    )
    def delete(self, request, pk):
        try:
            if not (request.user.is_staff or request.user.is_superuser):
                return Response(
                    {
                        "detail": (
                            "Only administrators can "
                            "delete categories."
                        )
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            category = self.get_object(pk)

            if not category:
                return Response(
                    {
                        "detail": "Category not found."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                category.delete()

            except Exception:
                return Response(
                    {
                        "detail": (
                            "Category cannot be deleted "
                            "because it is being used by courses."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            return Response(
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            logger.error(f"Category deletion error: {e}")
            return Response(
                {"detail": "An error occurred during category deletion."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )