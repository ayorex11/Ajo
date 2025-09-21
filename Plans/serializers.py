from rest_framework import serializers
from .models import SavingsPlan, Transaction

class SavingsPlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = SavingsPlan
        fields = '__all__'
        read_only_fields = ['user', 'date_created', 'plan_id', 'active', 'remaining_balance','date_started', 'number_of_payouts', 'number_of_payouts_left']


class TransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Transaction
        fields = '__all__'
