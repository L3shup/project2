from django.contrib import admin
from django.urls import path
from messenger.views import register_view, login_view
from messenger.soap_handler import soap_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', register_view),
    path('api/login/', login_view),
    path('soap/', soap_view),
]