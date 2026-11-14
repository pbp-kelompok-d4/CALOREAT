from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.html import strip_tags
from rest_framework import serializers

from main.models import Reviews, check_minimum_content


class ReviewsSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%d %b %Y", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Reviews
        fields = [
            "id",
            "customer_name",
            "profile_picture",
            "star",
            "content",
            "date",
            "can_edit",
        ]
        read_only_fields = [
            "id",
            "customer_name",
            "profile_picture",
            "date",
        ]

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return False
        return request.user.is_superuser or obj.created_by_id == request.user.id

    def validate_star(self, value):
        value = strip_tags(value).strip()
        valid_stars = {choice[0] for choice in Reviews.STAR_CHOICES}
        if value not in valid_stars:
            raise serializers.ValidationError("Rating must be between 1 and 5 stars.")
        return value

    def validate_content(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("The review cannot contain only HTML tags.")
        try:
            check_minimum_content(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        return value

    def create(self, validated_data):
        request = self.context.get("request")
        if (
            "created_by" not in validated_data
            and request is not None
            and request.user.is_authenticated
        ):
            validated_data["created_by"] = request.user

        if not validated_data.get("customer_name"):
            user = validated_data.get("created_by")
            if user is not None:
                raw_name = strip_tags(user.first_name).strip() if user.first_name else ""
                validated_data["customer_name"] = (raw_name or "Admin")[:25]
            else:
                validated_data["customer_name"] = "Guest"

        return super().create(validated_data)
