from Plans.models import SavingsPlan, Transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
import requests
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import hashlib
import hmac
import json
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

@csrf_exempt
@require_POST
@api_view(['POST'])
@permission_classes([AllowAny])
def paystack_webhook(request):
    """
    Paystack webhook to handle payment events
    """
    # Skip authentication for webhooks - Paystack can't authenticate
    paystack_secret = os.getenv('PAYSTACK_SECRET_KEY')
    signature = request.headers.get('x-paystack-signature')
    
    if not signature:
        return Response({'error': 'No signature'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify signature instead of using Django auth
    body = request.body.decode('utf-8')
    computed_signature = hmac.new(
        paystack_secret.encode('utf-8'),
        body.encode('utf-8'),
        digestmod=hashlib.sha512
    ).hexdigest()
    
    if not hmac.compare_digest(computed_signature, signature):
        return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Parse the webhook payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)
    
    event = payload.get('event')
    data = payload.get('data')
    
    # Handle different events
    if event == 'charge.success':
        return handle_successful_payment(data)
    elif event == 'charge.failed':
        return handle_failed_payment(data)
    else:
        # Log unhandled events
        print(f"Unhandled webhook event: {event}")
        return Response({'status': 'unhandled_event'}, status=status.HTTP_200_OK)

def handle_successful_payment(data):
    """
    Handle successful payment webhook
    """
    reference = data.get('reference')


    
    try:
        # Find the transaction
        transaction = Transaction.objects.get(
            transaction_reference=reference,
            completed=False
        )
        
        # Update transaction status
        transaction.completed = True
        transaction.save()
        

        if transaction.savings_plan:
            plan = transaction.savings_plan

            plan.active = True
            plan.save()
        
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
        
    except Transaction.DoesNotExist:
        # Log this for investigation
        print(f"Transaction with reference {reference} not found")
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log the error for investigation
        print(f"Error processing webhook: {str(e)}")
        return Response({'error': 'Processing error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def handle_failed_payment(data):
    """
    Handle failed payment webhook
    """
    reference = data.get('reference')
    
    try:
        transaction = Transaction.objects.get(transaction_reference=reference)
        transaction.completed = False
        transaction.save()
        
        return Response({'status': 'failed_handled'}, status=status.HTTP_200_OK)
        
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
