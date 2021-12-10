import math
from datetime import date, timedelta
import json

from django.http import HttpResponse
from django.db.models import F
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from api.models import User, IncomeSource, Income, Payment, Interval
from api.helpers import get_average_incomes, get_tax_dict
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
        for _ in range(i_to_add):
            i_l = Interval.objects.all().order_by('-end_date').first()
            n_sd = i_l.end_date + timedelta(days=1)
            n_ed = n_sd + timedelta(days=DAYS_IN_INTERVAL - 1)
            Interval.objects.create(start_date=n_sd, end_date=n_ed)

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


class IntervalPaymentsListView(APIView):
    def get(self, request, interval):
        payments = Payment.objects.filter(interval_id=interval)
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)


@api_view(['GET'])
def tax(request, interval):
    """ GET the tax due for a specific interval """
    return Response(get_tax_dict(interval))


@api_view(['GET'])
def income_per_interval(request, interval):
    i_t = Interval.objects.get(id=interval)
    incomes = Income.objects.filter(
        date__gte=i_t.start_date,
        date__lte=i_t.end_date).annotate(
        user=F('incomesource__user'))
    inc_array = [{'user': i.user, 'amount': i.amount,
                  'incomesource': i.incomesource.name} for i in incomes]
    users = incomes.values_list('user', flat=True).distinct()
    return_dict = {}
    for user in users:
        sources = {}
        for inc in inc_array:
            if inc['user'] == user:
                source_name = inc['incomesource']
                sources[source_name] = sources.get(
                    source_name, 0) + inc['amount']
        return_dict[user] = sources
    return Response(return_dict)


@api_view(['GET'])
def avg_income_per_interval(request, interval):
    avg_incs = get_average_incomes(interval)
    ret_dict = {}
    for inc in avg_incs:
        ret_dict[inc['user']] = inc['amount']
    return Response(ret_dict)
