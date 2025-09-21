from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import SavingsPlan, Transaction
from .serializers import SavingsPlanSerializer, TransactionSerializer, FilterTransactionsByDateSerializer
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
import random
from decimal import ROUND_UP

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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_savings_plans(request):
    user = request.user
    plans = SavingsPlan.objects.filter(user=user)
    serializer = SavingsPlanSerializer(plans, many=True)
    data = {'message':'success',
            'data': serializer.data}
    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])     
def get_saving_plan(request, plan_id):
    user = request.user
    try:
        plan = SavingsPlan.objects.get(user=user, plan_id=plan_id)
    except SavingsPlan.DoesNotExist:
        return Response({'error': 'Savings plan not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = SavingsPlanSerializer(plan)
    data = {'message':'success',
            'data': serializer.data}   
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_active_savings_plans(request):
    user = request.user
    plans = SavingsPlan.objects.filter(user=user, active=True)
    serializer = SavingsPlanSerializer(plans, many=True)
    data = {'message':'success',
            'data': serializer.data}
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_transactions(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user)
    serializer = TransactionSerializer(transactions, many=True)
    data = {'message':'success',
            'data': serializer.data}
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])  
@permission_classes([IsAuthenticated])

def get_deposit_transactions(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user, type='Deposit')
    serializer = TransactionSerializer(transactions, many=True)
    data = {'message':'success',
            'data': serializer.data}
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_withdrawal_transactions(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user, type='Withdrawal')
    serializer = TransactionSerializer(transactions, many=True)
    data = {'message':'success',
            'data': serializer.data}    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_completed_transactions(request):
    user = request.user
    transactions = Transaction.objects.filter(user=user, completed=True)
    serializer = TransactionSerializer(transactions, many=True)
    data = {'message':'success',
            'data': serializer.data}    
    return Response(data, status=status.HTTP_200_OK)


@swagger_auto_schema(methods=['GET'], query_serializer=FilterTransactionsByDateSerializer)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def filter_transactions_by_date(request):
    user = request.user
    serializer = FilterTransactionsByDateSerializer(data=request.query_params)
    
    serializer.is_valid(raise_exception=True)
    
    start_date = serializer.validated_data['start_date']
    end_date = serializer.validated_data['end_date']
    
    end_date_inclusive = end_date + timezone.timedelta(days=1)
    
    transactions = Transaction.objects.filter(
        user=user, 
        date_created__date__gte=start_date,
        date_created__date__lt=end_date_inclusive
    )
    
    serializer = TransactionSerializer(transactions, many=True)
    data = {
        'message': 'success',
        'count': transactions.count(),
        'data': serializer.data
    }    
    return Response(data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])

def get_transaction_by_reference(request, reference):
    user = request.user
    try:
        transaction = Transaction.objects.get(user=user, transaction_reference=reference)
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = TransactionSerializer(transaction)
    data = {'message':'success',
            'data': serializer.data}    
    return Response(data, status=status.HTTP_200_OK)