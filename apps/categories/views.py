from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .models import Category
from .serializers import CategorySerializer


class CategoryListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return [IsAuthenticated()]

    @extend_schema(
        operation_id="list_categories",
        description="List all active categories",
        responses={200: CategorySerializer(many=True)}
    )
    def get(self, request):

        categories = Category.objects.filter(
            is_active=True,
        ).select_related(
            "parent",
        )

        serializer = CategorySerializer(
            categories,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        operation_id="create_category",
        description="Create a new category (admin only)",
        request=CategorySerializer,
        responses={201: CategorySerializer}
    )
    def post(self, request):

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

        serializer = CategorySerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        category = serializer.save()

        return Response(
            CategorySerializer(category).data,
            status=status.HTTP_201_CREATED,
        )



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

    @extend_schema(
        operation_id="delete_category",
        description="Delete category (admin only)",
        responses={204: OpenApiResponse(description="Category deleted successfully")}
    )
    def delete(self, request, pk):

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