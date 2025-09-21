from django.urls import path
from . import views
urlpatterns = [
    path('verify_bvn/', views.verify_bvn, name='verify_bvn'),
]