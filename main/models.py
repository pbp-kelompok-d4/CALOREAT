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
    profile_picture = models.URLField(default=DEFAULT_PROFILE_PICTURE, editable=False)
    customer_name = models.CharField(max_length=25)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True, editable=False)
    star = models.CharField(max_length=5, choices=STAR_CHOICES, default='★★★★★')

    def save(self, *args, **kwargs):
        self.profile_picture = DEFAULT_PROFILE_PICTURE
        super().save(*args, **kwargs)

    def __str__(self):
        return self.customer_name