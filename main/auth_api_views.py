from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .forms import RegisterForm


@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    form = RegisterForm(request.data)
    if not form.is_valid():
        return Response({"errors": form.errors.get_json_data()}, status=400)
    form.save()
    return Response({"detail": "Akun berhasil dibuat. Silakan login."}, status=201)


@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    user = authenticate(
        username=request.data.get("email"),
        password=request.data.get("password"),
    )
    if user is None:
        return Response({"detail": "Email atau password salah."}, status=400)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        "token": token.key,
        "name": user.get_full_name(),
        "email": user.email,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_logout(request):
    request.user.auth_token.delete()
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_me(request):
    return Response({
        "name": request.user.get_full_name(),
        "email": request.user.email,
    })