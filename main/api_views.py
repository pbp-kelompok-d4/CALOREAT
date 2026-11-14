from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from main.models import Reviews
from main.permissions import IsReviewCreatorOrSuperuserDeleteOrReadOnly
from main.serializers import ReviewsSerializer

STAR_FILTER_MAP = {
    "5": "★★★★★",
    "4": "★★★★☆",
    "3": "★★★☆☆",
    "2": "★★☆☆☆",
    "1": "★☆☆☆☆",
}

REVIEW_PERMISSION_CLASSES = (IsReviewCreatorOrSuperuserDeleteOrReadOnly,)

# Reviews
def _check_object_permissions(request, obj, perm_classes=REVIEW_PERMISSION_CLASSES):
    for perm_cls in perm_classes:
        permission = perm_cls()
        if not permission.has_object_permission(request, None, obj):
            raise PermissionDenied(detail=getattr(permission, "message", None))


@api_view(["GET", "HEAD", "POST"])
@authentication_classes([SessionAuthentication])
@permission_classes(REVIEW_PERMISSION_CLASSES)
def review_list(request):
    if request.method in ("GET", "HEAD"):
        reviews = Reviews.objects.order_by("-date")
        star_filter = request.query_params.get("star", "").strip()
        mine_filter = request.query_params.get("mine", "").strip().lower()

        if star_filter:
            reviews = reviews.filter(star=STAR_FILTER_MAP.get(star_filter, star_filter))
        if mine_filter in ("1", "true"):
            if request.user.is_authenticated:
                reviews = reviews.filter(created_by=request.user)
            else:
                reviews = reviews.none()

        serializer = ReviewsSerializer(
            reviews,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    if Reviews.objects.filter(created_by=request.user).exists():
        return Response(
            {"detail": "You already have a review. Please delete it before adding another."},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = ReviewsSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    try:
        serializer.save()
    except IntegrityError:
        return Response(
            {"detail": "You already have a review. Please delete it before adding another."},
            status=status.HTTP_409_CONFLICT,
        )
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@authentication_classes([SessionAuthentication])
@permission_classes(REVIEW_PERMISSION_CLASSES)
def review_detail(request, review_id):
    review = get_object_or_404(Reviews, pk=review_id)
    _check_object_permissions(request, review)

    if request.method in ("GET", "HEAD"):
        serializer = ReviewsSerializer(review, context={"request": request})
        return Response(serializer.data)

    if request.method == "DELETE":
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = ReviewsSerializer(
        review,
        data=request.data,
        partial=request.method == "PATCH",
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
