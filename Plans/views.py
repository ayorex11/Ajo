from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import SavingsPlan, Transaction
from .serializers import SavingsPlanSerializer, TransactionSerializer
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
import random
from decimal import Decimal, ROUND_UP

def create_plan_id():
    return ''.join([str(random.randint(0, 9)) for _ in range(4)])

def unique_plan_id():
    while True:
        random_id = create_plan_id()
        if not SavingsPlan.objects.filter(plan_id = random_id).exists():
            break
    return random_id

@swagger_auto_schema(methods=['POST'], request_body=SavingsPlanSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_savings_plan(request):
    user = request.user
    serializer = SavingsPlanSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    valid_data = serializer.validated_data
    date_created = timezone.now()
    plan_id = unique_plan_id()
    active = False
    remaining_balance = valid_data['total_amount']
    if valid_data['set_payout'] >= valid_data['total_amount']:
        return Response({'error': 'Set payout must be less than total amount.'}, status=status.HTTP_400_BAD_REQUEST)
    if valid_data['set_payout'] <= 0 or valid_data['total_amount'] <= 0:
        return Response({'error': 'Amounts must be greater than zero.'}, status=status.HTTP_400_BAD_REQUEST)
    number_of_payouts = (valid_data['total_amount'] / valid_data['set_payout']).to_integral_value(rounding=ROUND_UP)
    number_of_payouts_left = number_of_payouts

    plan = SavingsPlan(user=user, 
                       date_created=date_created, 
                       plan_id=plan_id, 
                       active=active,
                        remaining_balance=remaining_balance,
                        number_of_payouts=number_of_payouts,
                        number_of_payouts_left=number_of_payouts_left, 
                         **valid_data)
    plan.save()

    response_data = SavingsPlanSerializer(plan)
    data = {'message':'success',
            'data': response_data.data}
    return Response(data, status=status.HTTP_201_CREATED)




