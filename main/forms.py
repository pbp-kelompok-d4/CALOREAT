from django.forms import ModelForm, TextInput

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
