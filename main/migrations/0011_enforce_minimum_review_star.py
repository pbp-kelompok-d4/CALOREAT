from django.db import migrations, models
from django.db.models import Q


def convert_zero_star_reviews(apps, schema_editor):
    Reviews = apps.get_model("main", "Reviews")
    Reviews.objects.filter(star="☆☆☆☆☆").update(star="★☆☆☆☆")


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0010_reviews_one_review_per_user"),
    ]

    operations = [
        migrations.RunPython(
            convert_zero_star_reviews,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="reviews",
            name="star",
            field=models.CharField(
                choices=[
                    ("★★★★★", "★★★★★"),
                    ("★★★★☆", "★★★★☆"),
                    ("★★★☆☆", "★★★☆☆"),
                    ("★★☆☆☆", "★★☆☆☆"),
                    ("★☆☆☆☆", "★☆☆☆☆"),
                ],
                default="★★★★★",
                max_length=5,
            ),
        ),
        migrations.AddConstraint(
            model_name="reviews",
            constraint=models.CheckConstraint(
                condition=Q(
                    star__in=[
                        "★☆☆☆☆",
                        "★★☆☆☆",
                        "★★★☆☆",
                        "★★★★☆",
                        "★★★★★",
                    ]
                ),
                name="review_star_at_least_one",
            ),
        ),
    ]
