from rest_framework import serializers
from api.models import User, Income, Payment, Interval


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'name']


class IncomeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Income
        fields = ['amount', 'date', 'incomesource']


class IntervalSerializer(serializers.ModelSerializer):

    class Meta:
        model = Interval
        fields = ['id', 'start_date', 'end_date', 'amount']


class UserIncomeSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'name']


class PaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = ['id', 'interval', 'user', 'amount']
