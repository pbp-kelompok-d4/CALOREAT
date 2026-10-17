from django.db import models
import uuid

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
    customer_name = models.CharField(max_length=25)
    content = models.TextField()
    date = models.DateTimeField(auto_now_add=True, editable=False)
    profile_picture = models.URLField(default="https://drive.google.com/thumbnail?id=1jQetxUJoI4cqaIimiiw1u2rkYLS5mInb&sz=w1000")
    star = models.CharField(max_length=5, choices=STAR_CHOICES, default='★★★★★')

    def __str__(self):
        return self.customer_name