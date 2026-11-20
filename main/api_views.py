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

from main.calorie_views import _needs
from main.models import CalorieProfile, PortionGuide, Reviews
from main.permissions import IsReviewCreatorOrSuperuserDeleteOrReadOnly, IsStaffOrReadOnly
from main.serializers import PortionGuideSerializer, ReviewsSerializer

STAR_FILTER_MAP = {
    "5": "★★★★★",
    "4": "★★★★☆",
    "3": "★★★☆☆",
    "2": "★★☆☆☆",
    "1": "★☆☆☆☆",
}

REVIEW_PERMISSION_CLASSES = (IsReviewCreatorOrSuperuserDeleteOrReadOnly,)


def _portion_context(user):
    nutrition_needs = {"complete": False, "bmr": None, "maintenance": None, "goal_kcal": None}
    if user.is_authenticated:
        profile = CalorieProfile.objects.filter(user=user).first()
        if profile is not None:
            nutrition_needs = _needs(profile)

    meal_targets = {}
    if nutrition_needs["complete"]:
        goal_kcal = nutrition_needs["goal_kcal"]
        meal_targets = {
            "breakfast": round(goal_kcal * 0.25),
            "lunch": round(goal_kcal * 0.35),
            "dinner": round(goal_kcal * 0.30),
        }
        meal_targets["snack"] = goal_kcal - sum(meal_targets.values())

    return {"nutrition_needs": nutrition_needs, "meal_targets": meal_targets}


@api_view(["GET", "HEAD", "POST"])
@permission_classes([IsStaffOrReadOnly])
def portion_guide_list(request):
    if request.method in ("GET", "HEAD"):
        guides = PortionGuide.objects.all()
        meal_type = request.query_params.get("meal_type", "").strip()
        valid_meal_types = {choice[0] for choice in PortionGuide.MEAL_CHOICES}
        if meal_type in valid_meal_types:
            guides = guides.filter(meal_type=meal_type)

        context = _portion_context(request.user)
        serializer = PortionGuideSerializer(
            guides,
            many=True,
            context={**context, "request": request},
        )
        return Response({**context, "guides": serializer.data})

    serializer = PortionGuideSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET", "HEAD", "PUT", "PATCH", "DELETE"])
@permission_classes([IsStaffOrReadOnly])
def portion_guide_detail(request, guide_id):
    guide = get_object_or_404(PortionGuide, pk=guide_id)
    context = _portion_context(request.user)

    if request.method in ("GET", "HEAD"):
        serializer = PortionGuideSerializer(
            guide,
            context={**context, "request": request},
        )
        return Response(serializer.data)

    if request.method == "DELETE":
        guide.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = PortionGuideSerializer(
        guide,
        data=request.data,
        partial=request.method == "PATCH",
        context={**context, "request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)

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
