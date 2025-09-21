from rest_framework import serializers

class VerificationSerializer(serializers.Serializer):
    BVN  = serializers.CharField()
