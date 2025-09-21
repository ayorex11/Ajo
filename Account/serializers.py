from rest_framework import serializers
from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from dj_rest_auth.serializers import UserDetailsSerializer
from .models import User
from django.db import IntegrityError

def email_address_exists(email):
    return User.objects.filter(email=email).exists()


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=True, write_only=True)
    last_name = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(required=allauth_settings.EMAIL_REQUIRED)
    username = serializers.CharField(required=True, write_only=True)
    phone_number = serializers.CharField(max_length=25, required=True, write_only=True)
    password1 = serializers.CharField(required=True, write_only=True)
    password2 = serializers.CharField(required=True, write_only=True)

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    ("A user is already registered with this e-mail address."))
        return email

    def validate_password1(self, password):
        return get_adapter().clean_password(password)

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError(
                ("The two password fields didn't match."))

        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError(
                {"email": "A user is already registered with this email address."})
        if User.objects.filter(phone_number=data['phone_number']).exists():
            raise serializers.ValidationError(
                {"phone_number": "This phone number is already in use."})
        return data

    def get_cleaned_data(self):
        return {
            'password1': self.validated_data.get('password1', ''),
            'email': self.validated_data.get('email', ''),
            'username': self.validated_data.get('username', ''),
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'phone_number': self.validated_data.get('phone_number', ''),
        }
    
    def save(self, request):
        adapter = get_adapter()
        user = adapter.new_user(request)
        self.cleaned_data = self.get_cleaned_data()
        adapter.save_user(request, user, self)
        setup_user_email(request, user, [])

        
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        phone_number = self.cleaned_data.get('phone_number')

        user.first_name = first_name
        user.last_name = last_name
        user.phone_number = phone_number
        
        try:
            user.save()
        except IntegrityError as e:
            if 'unique constraint' in str(e).lower() and 'phone_number' in str(e).lower():
                raise serializers.ValidationError("This phone number is already in use.")
            else:
                raise serializers.ValidationError("Error while saving user.")
        return user

class UserDetailsSerializer(UserDetailsSerializer):
    
    class Meta:
        fields = ['email', 'first_name', 'last_name','phone_number']
        read_only_fields = ['email']
        model = User

        
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'email', 'date_joined','first_name', 'last_name', 'phone_number']
