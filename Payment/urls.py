from . import views
from django.urls import path

urlpatterns = [
    path('initialize_deposit/', views.initialize_deposit),
]