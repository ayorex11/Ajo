from django.urls import path
from . import views

urlpatterns = [
    path('savings-plans/', views.create_savings_plan),
    path('filter_transactions_by_date/', views.filter_transactions_by_date),
    path('get_savings_plans/', views.get_savings_plans),
    path('get_saving_plan/<str:plan_id>/', views.get_saving_plan),
    path('get_transactions/', views.get_transactions),
    path('get_deposit_transactions/', views.get_deposit_transactions),
    path('get_withdrawal_transactions/', views.get_withdrawal_transactions),
    path('get_completed_transactions/', views.get_completed_transactions),
    path('get_transaction_by_reference/<str:transaction_reference>/', views.get_transaction_by_reference),
    path('get_active_savings_plans/', views.get_active_savings_plans),
]