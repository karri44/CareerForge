from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'phone', 'company_name']

    def validate(self, attrs):
        user = User(username=attrs.get('username',''), email=attrs.get('email',''))
        try:
            validate_password(attrs['password'], user=user)
        except ValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        if attrs.get('role') == 'EMPLOYER' and not attrs.get('company_name'):
            raise serializers.ValidationError({'company_name':'Company name is required.'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data['role'],
            phone=validated_data.get('phone', ''),
            company_name=validated_data.get('company_name', ''),
        )
        return user