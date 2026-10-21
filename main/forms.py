from django.forms import ModelForm, TextInput
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from main.models import Reviews

class ReviewsForm(ModelForm):
    class Meta:
        model = Reviews
        fields = [
            "customer_name",
            "star",
            "content",
        ]

        labels = {
            "customer_name": "Masukkan nama kamu",
            "star": "★★★★★",
            "content": "Isi review"
        }

        widgets = {
            "customer_name": TextInput(
                attrs={
                    "placeholder": "Nama",
                }
            ),
            "star": TextInput(
                attrs={
                    "placeholder": "★★★★★",
                }
            ),
            "content": TextInput(
                attrs={
                    "placeholder": "Isi review",
                }
            ),
        }

    def clean_title(self):
        title = strip_tags(self.cleaned_data["content"]).strip()
        if not title:
            raise ValidationError("Isi reviews tidak boleh hanya berisi tag HTML.")
        return title
