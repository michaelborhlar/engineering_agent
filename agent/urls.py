from django.urls import path
from . import views

urlpatterns = [
    path("webhook/", views.telex_webhook, name="telex_webhook"),
    path("health/", views.health, name="health"),
]
