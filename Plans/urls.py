from django.urls import path
from . import views

urlpatterns = [
    path('savings-plans/', views.create_savings_plan),
]