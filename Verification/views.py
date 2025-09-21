from django.shortcuts import render
from .serializers import VerificationSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import requests
import os
import logging
from drf_yasg.utils import swagger_auto_schema
from django.conf import settings
from django.utils import timezone
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class BVNVerificationError(Exception):
    """Custom exception for BVN verification errors"""
    pass

@swagger_auto_schema(methods=['POST'], request_body=VerificationSerializer())
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_bvn(request):
    serializer = VerificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user is already verified
    if request.user.verified:
        return Response({
            'message': 'User is already verified'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    bvn = serializer.validated_data['BVN']
    
    # Prepare API request
    url = f"https://api.sandbox.youverify.co/v2/api/identity/ng/bvn"
    headers = {
        "token": os.getenv('VERIFICATION'),
        "Content-Type": "application/json"
    }
    request_body = {
        'id': bvn,
        'premiumNin': False,
        'isSubjectConsent': True,
    }
    
    try:
        # Make external API call with timeout
        response = requests.post(url, headers=headers, json=request_body, timeout=15)
        response.raise_for_status()  # Raises exception for 4xx/5xx status codes
        
        response_data = response.json()
        
        # Log the API response (mask sensitive data in production)
        if settings.DEBUG:
            logger.info(f"BVN API Response: {json.dumps(response_data)}")
        
        # Check if BVN was found
        if response_data.get('data', {}).get('status') != 'found':
            return Response({
                'message': 'BVN not found or invalid',
                'error': response_data.get('message', 'Unknown error')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Extract BVN data
        bvn_data = response_data['data']
        
        # Verify user information matches
        user = request.user
        
        # Format user's date of birth to match API format (YY-MM-DD)
        user_dob_formatted = user.date_of_birth.strftime('%y-%m-%d') if user.date_of_birth else None
        
        # Compare user details with BVN information
        name_matches = (
            bvn_data.get('firstName', '').lower() == user.first_name.lower() and
            bvn_data.get('lastName', '').lower() == user.last_name.lower()
        )
        
        dob_matches = bvn_data.get('dateOfBirth') == user_dob_formatted
        
        if name_matches and dob_matches:
            # Update user verification status
            user.verified = True
            user.verification_date = timezone.now()
            user.save()
            
            # Log successful verification
            logger.info(f"User {user.id} successfully verified with BVN")
            
            return Response({
                'message': 'BVN verified successfully',
                'data': {
                    'firstName': bvn_data.get('firstName'),
                    'lastName': bvn_data.get('lastName'),
                    'dateOfBirth': bvn_data.get('dateOfBirth'),
                    # Include other non-sensitive data as needed
                }
            }, status=status.HTTP_200_OK)
        else:
            # Log verification failure due to mismatched data
            logger.warning(f"BVN verification failed for user {user.id}: data mismatch")
            
            # Generic error message to avoid revealing specific mismatch details
            return Response({
                'message': 'Verification failed. Your information does not match our records.',
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except requests.exceptions.Timeout:
        logger.error(f"BVN verification timeout for user {request.user.id}")
        return Response({
            'message': 'Verification service is temporarily unavailable. Please try again later.',
        }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during BVN verification for user {request.user.id}: {str(e)}")
        return Response({
            'message': 'An error occurred while verifying BVN. Please try again later.',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except (KeyError, ValueError) as e:
        logger.error(f"Unexpected response format during BVN verification: {str(e)}")
        return Response({
            'message': 'Verification service returned an unexpected response.',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)