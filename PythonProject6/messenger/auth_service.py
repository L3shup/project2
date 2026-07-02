from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .database import User

def register_user(username, password, email=None):
    if User.objects.filter(username=username).exists():
        return None, "Username already exists"
    user = User.objects.create_user(username=username, password=password, email=email)
    return user, "User created"

def login_user(username, password):
    user = authenticate(username=username, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, "Login successful"
    return None, "Invalid credentials"