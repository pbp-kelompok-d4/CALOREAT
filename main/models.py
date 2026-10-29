from django.db import models
import uuid

DEFAULT_PROFILE_PICTURE = (
    "https://drive.google.com/thumbnail?"
    "id=1jQetxUJoI4cqaIimiiw1u2rkYLS5mInb&sz=w1000"
)

# Create your models here.
class Reviews(models.Model):
    STAR_CHOICES = [
        ('★★★★★', '★★★★★'),
        ('★★★★☆', '★★★★☆'),
        ('★★★☆☆', '★★★☆☆'),
        ('★★☆☆☆', '★★☆☆☆'),
        ('★☆☆☆☆', '★☆☆☆☆'),
        ('☆☆☆☆☆', '☆☆☆☆☆'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
    )
    profile_picture = models.URLField(default=DEFAULT_PROFILE_PICTURE, editable=False)
    customer_name = models.CharField(max_length=25)
    content = models.TextField(max_length=500)
    date = models.DateTimeField(auto_now_add=True, editable=False)
    star = models.CharField(max_length=5, choices=STAR_CHOICES, default='★★★★★')

    def save(self, *args, **kwargs):
        self.profile_picture = DEFAULT_PROFILE_PICTURE
        super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_name

class CalorieProfile(models.Model):
    SEX_CHOICES = (("male", "Male"), ("female", "Female"))
    ACTIVITY_CHOICES = (
        ("sedentary", "Sedentary"),
        ("light", "Lightly active"),
        ("moderate", "Moderately active"),
        ("active", "Active"),
    )
    GOAL_CHOICES = (
        ("lose_025", "Lose 0.25 kg / week"),
        ("lose_05", "Lose 0.5 kg / week"),
        ("maintain", "Maintain weight"),
        ("gain_025", "Gain 0.25 kg / week"),
    )

    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="calorie_profile")
    sex = models.CharField(max_length=8, choices=SEX_CHOICES, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    activity_level = models.CharField(max_length=12, choices=ACTIVITY_CHOICES, blank=True)
    goal = models.CharField(max_length=12, choices=GOAL_CHOICES, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Calorie profile for {self.user}"


class FoodEntry(models.Model):
    MEAL_CHOICES = (
        ("breakfast", "Breakfast"),
        ("lunch", "Lunch"),
        ("dinner", "Dinner"),
        ("snack", "Snacks"),
    )
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="food_entries")
    date = models.DateField()
    meal = models.CharField(max_length=12, choices=MEAL_CHOICES)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=160, blank=True)
    off_code = models.CharField(max_length=32, blank=True)
    grams = models.DecimalField(max_digits=7, decimal_places=1)
    kcal_100g = models.DecimalField(max_digits=6, decimal_places=1)
    protein_100g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    carbs_100g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    fat_100g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    nutriscore = models.CharField(max_length=1, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [models.Index(fields=("user", "date"), name="food_user_date_idx")]

    @property
    def kcal(self):
        return float(self.kcal_100g * self.grams / 100)

    def __str__(self):
        return f"{self.name} ({self.grams} g) - {self.user}"

class PortionGuide(models.Model):
    MEAL_CHOICES = [
        ("breakfast", "Breakfast"),
        ("lunch", "Lunch"),
        ("dinner", "Dinner"),
        ("snack", "Snack"),
    ]

    title = models.CharField(max_length=120)
    meal_type = models.CharField(
        max_length=12,
        choices=MEAL_CHOICES,
    )
    description = models.TextField()
    vegetables = models.CharField(max_length=200)
    protein = models.CharField(max_length=200)
    carbohydrates = models.CharField(max_length=200)
    image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["meal_type", "title"]

    def __str__(self):
        return self.title