
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from main.forms import PortionGuideForm
from main.models import PortionGuide
from main.calorie_views import _needs, _profile_for


@login_required(login_url="/login/")
def portion_guidance(request):
    guides = PortionGuide.objects.all()

    meal_type = request.GET.get("meal_type", "")
    if meal_type in dict(PortionGuide.MEAL_CHOICES):
        guides = guides.filter(meal_type=meal_type)

    profile = _profile_for(request.user)
    needs = _needs(profile)

    meal_percentages = {
        "breakfast": 25,
        "lunch": 35,
        "dinner": 30,
        "snack": 10,
    }

    meal_targets = {}
    if needs["complete"]:
        goal_kcal = needs["goal_kcal"]

        meal_targets = {
            "breakfast": round(goal_kcal * 0.25),
            "lunch": round(goal_kcal * 0.35),
            "dinner": round(goal_kcal * 0.30),
        }
        meal_targets["snack"] = (
            goal_kcal - sum(meal_targets.values())
        )
    guides = list(guides)

    for guide in guides:
        guide.personalized_portions = None

        target_kcal = meal_targets.get(guide.meal_type)

        if (
            target_kcal
            and guide.reference_kcal > 0
            and guide.vegetables_grams > 0
            and guide.protein_grams > 0
            and guide.carbohydrates_grams > 0
        ):
            scale = target_kcal / guide.reference_kcal

            guide.personalized_portions = {
                "target_kcal": target_kcal,
                "vegetables_grams": round(
                    guide.vegetables_grams * scale
                ),
                "protein_grams": round(
                    guide.protein_grams * scale
                ),
                "carbohydrates_grams": round(
                    guide.carbohydrates_grams * scale
                ),
            }

    context = {
        "guides": guides,
        "meal_choices": PortionGuide.MEAL_CHOICES,
        "selected_meal": (
            meal_type
            if meal_type in dict(PortionGuide.MEAL_CHOICES)
            else ""
        ),
        "nutrition_needs": needs,
        "meal_targets": meal_targets,
        "meal_percentages": meal_percentages,
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return render(
            request,
            "components/portion_guide_list.html",
            context,
        )

    return render(request, "portion_guidance.html", context)


@login_required(login_url="/login/")
def portion_create(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to create portion guides.")

    form = PortionGuideForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Portion guide created successfully.")
        return redirect("main:portion_guidance")

    return render(
        request,
        "portion_guidance_form.html",
        {
            "form": form,
            "page_title": "Create Portion Guide",
            "submit_label": "Create",
        },
    )


@login_required(login_url="/login/")
def portion_edit(request, guide_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to edit portion guides.")

    guide = get_object_or_404(PortionGuide, pk=guide_id)
    form = PortionGuideForm(request.POST or None, instance=guide)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Portion guide updated successfully.")
        return redirect("main:portion_guidance")

    return render(
        request,
        "portion_guidance_form.html",
        {
            "form": form,
            "page_title": "Edit Portion Guide",
            "submit_label": "Save Changes",
        },
    )


@login_required(login_url="/login/")
@require_POST
def portion_delete(request, guide_id):
    if not request.user.is_staff:
        return HttpResponseForbidden("You do not have permission to delete portion guides.")

    guide = get_object_or_404(PortionGuide, pk=guide_id)
    guide.delete()
    messages.success(request, "Portion guide deleted successfully.")
    return redirect("main:portion_guidance")
