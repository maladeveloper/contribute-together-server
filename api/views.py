import math
from datetime import date, timedelta
import json

from django.http import HttpResponse
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.models import User, IncomeSource, Income, Payment, Interval, NumericalParams
from api.helpers import get_average_incomes, get_tax_dict, has_all_income_submitted, get_income_unsubmitted_users, submit_income_as_payment
from api.serializers import (
    UserSerializer, UserIncomeSourceSerializer, IncomeSerializer,
    PaymentSerializer, IntervalSerializer
)
# pylint: disable=unused-argument,no-self-use

DAYS_IN_INTERVAL = 14

# Create your views here.


def index(request):
    return HttpResponse('Hello world')

# PATCH


@api_view(['PATCH'])
def change_interval_amount(request, interval):
    new_amount = json.loads(request.body.decode('utf-8'))['amount']
    i = Interval.objects.get(id=interval)
    i.amount = new_amount
    i.save()
    return HttpResponse(status=204)


# POST


class IncomeView(generics.CreateAPIView):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer


class PaymentView(generics.CreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer


# GET


class IntervalLatestListView(APIView):
    def add_latest_intervals(self, c_d, l_i):
        d_d = c_d - l_i.end_date
        i_to_add = math.ceil(d_d.days / DAYS_IN_INTERVAL)
        default_interval_amount = NumericalParams.objects.get(pk='default_interval_amount').value
        for _ in range(i_to_add):
            i_l = Interval.objects.all().order_by('-end_date').first()
            n_sd = i_l.end_date + timedelta(days=1)
            n_ed = n_sd + timedelta(days=DAYS_IN_INTERVAL - 1)
            Interval.objects.create(start_date=n_sd, end_date=n_ed, amount=default_interval_amount)

    def get(self, request):
        l_i = Interval.objects.all().order_by('-end_date').first()
        # Check if the current date is inside the latest interval
        c_d = date.today()
        if c_d > l_i.end_date:
            self.add_latest_intervals(c_d, l_i)
        intervals = Interval.objects.all().order_by('-end_date')
        serializer = IntervalSerializer(intervals, many=True)
        return Response(serializer.data)


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserIncomeSourceListView(APIView):
    def get(self, request, user):
        income_sources = IncomeSource.objects.filter(user_id=user)
        serializer = UserIncomeSourceSerializer(income_sources, many=True)
        return Response(serializer.data)


# Specified by interval

@api_view(['GET'])
def payment(request, interval):
    payment_dict = {}
    payments = Payment.objects.filter(interval_id=interval)
    for payment in payments:
        payment_dict[payment.user.id] = payment.amount

    return Response(payment_dict)


@api_view(['GET'])
def tax(request, interval):
    """ GET the tax due for a specific interval """
    if not has_all_income_submitted(interval):
        return Response({}, status=status.HTTP_403_FORBIDDEN)

    tax_dict = get_tax_dict(interval)
    submit_income_as_payment(interval, tax_dict)

    return Response(tax_dict)


@api_view(['GET'])
def income_per_interval(request, interval):
    i_t = Interval.objects.get(id=interval)
    return_dict = {}
    for user in User.objects.all():
        incomesources = IncomeSource.objects.filter(user=user)
        user_source = {}
        for inc_source in incomesources:
            incomes = Income.objects.filter(date__gte=i_t.start_date, date__lte=i_t.end_date, incomesource=inc_source)
            if len(incomes) > 0:
                amount = sum([i.amount for i in incomes])
                inc_ids = [i.id for i in incomes]
                user_source[inc_source.name] = {'amount': amount, 'ids': inc_ids}
        if len(user_source) > 0:
            return_dict[user.id] = user_source
    return Response(return_dict)


@api_view(['GET'])
def avg_income_per_interval(request, interval):
    avg_incs = get_average_incomes(interval)
    ret_dict = {}
    for inc in avg_incs:
        ret_dict[inc['user']] = inc['amount']
    return Response(ret_dict)


@api_view(['GET'])
def unsubmitted_users_per_interval(request, interval):
    unsubmitted, _ = get_income_unsubmitted_users(interval)
    unsubmitted_arr = sorted(unsubmitted)
    return Response(unsubmitted_arr)


@api_view(['GET'])
def total_income_by_interval(request):
    return_dict, all_intervals = {}, Interval.objects.all()
    for i_o in all_intervals:
        sd, ed = i_o.start_date, i_o.end_date
        key = str(sd) + '_' + str(ed)
        return_dict[key], income_per_user = {}, {}
        for user in User.objects.all():
            income_per_user[user.id] = Income.objects.filter(
                date__gte=sd, date__lte=ed, incomesource__user__id=user.id
            ).aggregate(Sum('amount'))['amount__sum']
        return_dict[key] = income_per_user
    return Response(return_dict)


@api_view(['GET'])
def total_tax_by_interval(request):
    return_dict, all_intervals = {}, Interval.objects.all()
    for i_o in all_intervals:
        sd, ed = i_o.start_date, i_o.end_date
        key = str(sd) + '_' + str(ed)
        return_dict[key] = get_tax_dict(i_o.id)
    return Response(return_dict)


# DELETE


@api_view(['DELETE'])
def delete_specific_income(request, income):
    get_object_or_404(Income, pk=income).delete()
    return Response({'message': 'Delete income' + str(income)}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'PATCH'])
def numerical_params(request):
    if request.method == 'GET':
        params_dict = {}
        for numerical_param in NumericalParams.objects.all():
            params_dict[numerical_param.key] = numerical_param.value
        return Response(params_dict)

    elif request.method == 'PATCH':
        patch_data = json.loads(request.body.decode('utf-8'))
        key = patch_data.get('key', None)
        value = patch_data.get('value', None)

        if key is None or value is None:
            return Response({'message': 'Missing key or value.'}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(value, int):
            return Response({'message': 'Value is not an integer.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            param = NumericalParams.objects.get(pk=key)
        except NumericalParams.DoesNotExist:
            return Response({'message': 'Key does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        param.value = value
        param.save()

        return Response({'message': 'Patch success.'}, status=status.HTTP_200_OK)
