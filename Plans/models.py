from django.db import models
from Account.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal

class SavingsPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_savings_plans')
    name = models.CharField(max_length=250, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    plan_id = models.CharField(max_length=10, unique=True, blank=True)
    frequency_choices = (
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
    )
    frequency = models.CharField(choices=frequency_choices, max_length=30, blank=False, null=False)
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places= 2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    set_payout = models.DecimalField(
        max_digits= 12,
        decimal_places= 2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    remaining_balance = models.DecimalField(
        max_digits= 12,
        decimal_places= 2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    number_of_payouts = models.PositiveIntegerField(default=0)
    number_of_payouts_left = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=False)
    date_started = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name + ' ' + self.user.first_name


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_transactions')
    transaction_types = (
        ('Deposit', 'Deposit'),
        ('Withdrawal', 'Withdrawal')
    )
    type = models.CharField(choices=transaction_types, max_length=30, null=False, blank=False)
    date_created = models.DateTimeField()
    savings_plan = models.ForeignKey(SavingsPlan, on_delete=models.CASCADE, related_name='savings_plan_transaction')
    completed = models.BooleanField(default=False)
    amount = models.DecimalField(
        max_digits= 12,
        decimal_places= 2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    fee = models.DecimalField(
        max_digits= 12,
        decimal_places= 2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    amount_paid = models.DecimalField(
        max_digits= 12,
        decimal_places= 2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    transaction_reference = models.CharField(max_length=250, blank=False, null=False)

    def __str__(self):
        return self.type
    