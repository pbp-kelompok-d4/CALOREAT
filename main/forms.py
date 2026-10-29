from django.forms import ModelForm, TextInput, Form
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from main.models import Reviews, PortionGuide
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import AuthenticationForm

class RegisterForm(Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Your name"}),
    )
    email = forms.EmailField(
        max_length=150,
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}),
    )
    password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("Email ini sudah terdaftar.")
        return email

    def clean_password(self):
        password = self.cleaned_data["password"]
        validate_password(password)
        return password

    def save(self):
        email = self.cleaned_data["email"]
        return User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data["full_name"],
        )
    
class LoginForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Email atau password salah.",
    }
    remember_me = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget.attrs.update(
            {"placeholder": "you@example.com", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update(
            {"placeholder": "Enter your password"}
        )
        
class ReviewsForm(ModelForm):
    class Meta:
        model = Reviews
        fields = [
            "customer_name",
            "star",
            "content",
        ]

        labels = {
            "customer_name": "Enter your name",
            "star": "★★★★★",
            "content": "Review"
        }

        widgets = {
            "customer_name": TextInput(
                attrs={
                    "placeholder": "Name",
                }
            ),
            "star": TextInput(
                attrs={
                    "placeholder": "★★★★★",
                }
            ),
            "content": TextInput(
                attrs={
                    "placeholder": "Write your review",
                }
            ),
        }

    def clean_title(self):
        title = strip_tags(self.cleaned_data["content"]).strip()
        if not title:
            raise ValidationError("The review cannot contain only HTML tags.")
        return title

class PortionGuideForm(forms.ModelForm):
    reference_kcal = forms.IntegerField(
        min_value=1,
        max_value=2000,
        label="Reference Meal Calories (kcal)",
        help_text="Calories represented by the reference portions.",
    )

    vegetables_grams = forms.IntegerField(
        min_value=1,
        max_value=2000,
        label="Vegetables (grams)",
        help_text="Reference serving size for vegetables.",
    )

    protein_grams = forms.IntegerField(
        min_value=1,
        max_value=2000,
        label="Protein Food (grams)",
        help_text="Reference serving size for protein.",
    )

    carbohydrates_grams = forms.IntegerField(
        min_value=1,
        max_value=2000,
        label="Carbohydrate Food (grams)",
        help_text="Reference serving size for carbohydrates.",
    )
    class Meta:
        model = PortionGuide
        fields = [
            "title",
            "meal_type",
            "description",
            "vegetables",
            "vegetables_grams",
            "protein",
            "protein_grams",
            "carbohydrates",
            "carbohydrates_grams",
            "reference_kcal",
            "image_url",
        ]
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "e.g. Balanced Lunch Plate",
            }),
            "description": forms.Textarea(attrs={
                "placeholder": "Describe the purpose of this portion guide",
                "rows": 4,
            }),
            "vegetables": forms.TextInput(attrs={
                "placeholder": "e.g. Half the plate",
            }),
            "protein": forms.TextInput(attrs={
                "placeholder": "e.g. A quarter of the plate",
            }),
            "carbohydrates": forms.TextInput(attrs={
                "placeholder": "e.g. A quarter of the plate",
            }),
            "image_url": forms.URLInput(attrs={
                "placeholder": "Optional image URL",
            }),
        }