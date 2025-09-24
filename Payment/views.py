from Plans.models import SavingsPlan, Transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
import requests
from rest_framework.permissions import IsAuthenticated
from .serializers import DepositSerializer
import os
from drf_yasg.utils import swagger_auto_schema
from Account.models import User
from django.utils import timezone

@swagger_auto_schema(methods=['POST'], request_body=DepositSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])

def initialize_deposit(request):
    user = request.user
    serializer = DepositSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    amount = serializer.validated_data['amount']
    email = serializer.validated_data['email']
    plan_id = serializer.validated_data['plan_id']

    plan = SavingsPlan.objects.get(user=user, plan_id=plan_id)
    if not plan:
        return Response({'message': 'Savings plan not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if plan.total_amount != amount:
        return Response({'message': 'amount does not match savings plan total amount'}, status=status.HTTP_400_BAD_REQUEST) 
    if user.email != email:
        return Response({'message': 'email address not valid'}, status=status.HTTP_404_NOT_FOUND)
    
    url = "https://api.paystack.co/transaction/initialize"
    headers = {"authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}"}
    request_body = {
        'amount' : int(amount * 100) + (100*100),
        'email' : email,
    }
    r = requests.post(url, headers=headers, json=request_body)
    r.raise_for_status()
    response = r.json()
    
    Transaction.objects.create(
        user = user,
        type = 'Deposit',
        date_created = timezone.now(),
        savings_plan = plan,
        amount = amount,
        fee = 100,
        amount_paid = amount + 100,
        transaction_reference = response['data']['reference'],
        completed = False
    )
    data = {'message': 'Transaction initiated. Service fee of 100 naira added.',
            'data': response}
    
    return Response(data, status=status.HTTP_200_OK)