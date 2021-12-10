import json
from datetime import date, timedelta

from django.forms.models import model_to_dict
from django.test import TestCase, Client
from rest_framework import status

from ..models import User, IncomeSource, Income, Interval, Payment

# pylint: disable=no-self-use

# initialize the APIClient app
client = Client()

# PATCH


class ChangeIntervalAmount(TestCase):
    def set_up(self):
        User.objects.create(id='TEST000', name='Test')
        Interval.objects.create(
            start_date='2021-10-04', end_date='2021-10-17')

    def test_changing_latest_interval(self):
        self.set_up()
        interval = Interval.objects.first()
        new_amount = 1234
        amount_obj = {'amount': new_amount}

        response = client.patch(
            '/api/interval/' + str(interval.id) + '/amount/',
            json.dumps(amount_obj),
            content_type='application/json'
        )
        self.assertEqual(
            Interval.objects.get(id=interval.id).amount,
            new_amount
        )
        self.assertEqual(response.status_code, 204)

# POST


class IncomeTest(TestCase):
    def setUp(self):
        user = User.objects.create(id='TEST000', name='Test')
        IncomeSource.objects.create(
            name='TestIncomeSource', user_id=user.id)

    def test_post_income(self):
        income_source = IncomeSource.objects.first()
        income_obj = {
            'incomesource': income_source.id,
            'amount': 99,
            'date': '2021-10-07'}
        response = client.post(
            '/api/income/',
            json.dumps(income_obj),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        inc_from_db = model_to_dict(Income.objects.first())
        del inc_from_db['id']
        inc_from_db['date'] = inc_from_db['date'].strftime('%Y-%m-%d')
        self.assertEqual(inc_from_db, income_obj)


class PaymentTest(TestCase):
    def setUp(self):
        User.objects.create(id='TEST000', name='Test')
        Interval.objects.create(
            start_date='2021-10-04', end_date='2021-10-17')

    def test_post_payment(self):
        interval = Interval.objects.first()
        user = User.objects.first()
        payment_obj = {'interval': interval.id, 'user': user.id, 'amount': 99}
        response = client.post(
            '/api/payment/',
            json.dumps(payment_obj),
            content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        pay_from_db = model_to_dict(Payment.objects.first())
        del pay_from_db['id']
        self.assertEqual(pay_from_db, payment_obj)


# GET


class UserListTest(TestCase):
    """ GET All the Users API """
    user_keys = ['id', 'name']

    def setUp(self):
        for i in range(3):
            User.objects.create(id='TES000' + str(i), name='Test ' + str(i))

    def test_get_all_users(self):
        # get API response
        response = client.get('/api/users/')
        # get from db
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        suffix = 0
        for user in response.data:
            self.assertEqual(
                dict(user), {
                    'id': 'TES000' + str(suffix), 'name': 'Test ' + str(suffix)})
            suffix += 1


class IntervalListTest(TestCase):
    def create_intervals(self):
        # Create a seed interval far in the past
        s_d = date.today()
        Interval.objects.create(
            start_date=s_d - timedelta(61),
            end_date=s_d - timedelta(48))
        return Interval.objects.create(
            start_date=s_d - timedelta(47),
            end_date=s_d - timedelta(34))

    def test_get_intervals(self):
        self.create_intervals()
        client.get('/api/intervals/', follow=True)
        s_d = date.today()
        i_s = Interval.objects.all().order_by('-end_date')
        self.assertEqual(
            sorted([*model_to_dict(i_s[0])]),
            sorted(['end_date', 'start_date', 'id', 'amount'])
        )
        self.assertEqual(len(i_s), 5)
        l_i = i_s.first()
        self.assertEqual(l_i.end_date, s_d + timedelta(8))
        self.assertEqual(l_i.start_date, s_d - timedelta(5))


class UserIncomeSourceListTest(TestCase):
    """ GET the sources of income given an user's Id"""

    def setUp(self):
        User.objects.create(id='TEST000', name='Test')
        IncomeSource.objects.create(name='TestIncomeSource', user_id='TEST000')

    def test_get_user_income_sources(self):
        response = client.get('/api/income-sources/TEST000/')
        self.assertEqual(response.data[0]['name'], 'TestIncomeSource')
        self.assertEqual(
            list(
                response.data[0].keys()).sort(), [
                'name', 'id'].sort())

# Specified by interval


class IntervalPaymentsTest(TestCase):
    def create_models(self):
        # Create an interval for payment to be associated with
        interval = Interval.objects.create(
            start_date='2021-09-06', end_date='2021-09-19')

        # Create 3 users to associate the intervals with
        user0 = User.objects.create(id='TEST000', name='Test0')
        user1 = User.objects.create(id='TEST001', name='Test1')
        user2 = User.objects.create(id='TEST002', name='Test2')

        # Create payments associated with each user and the interval
        Payment.objects.create(
            user_id=user0.id, interval_id=interval.id, amount=10)
        Payment.objects.create(
            user_id=user1.id, interval_id=interval.id, amount=10)
        Payment.objects.create(
            user_id=user2.id, interval_id=interval.id, amount=10)
        return interval

    def test_get_payments_per_existing_interval(self):
        interval = self.create_models()
        db_pays = Payment.objects.all()
        response = client.get('/api/payment/' + str(interval.id), follow=True)
        expected_pays = sorted([model_to_dict(pay)
                               for pay in db_pays], key=lambda d: d['id'])
        received_pays = sorted([dict(pay)
                               for pay in response.data], key=lambda d: d['id'])
        self.assertEqual(expected_pays, received_pays)
        self.assertEqual(len(response.data), 3)

    def test_get_payments_per_non_existing_interval(self):
        interval = self.create_models()
        response = client.get(
            '/api/payment/' + str(interval.id + 999), follow=True)
        self.assertEqual(len(response.data), 0)


class TaxTest(TestCase):
    def create_models(self):
        user0 = User.objects.create(id='TEST000', name='Test0')
        user1 = User.objects.create(id='TEST001', name='Test1')
        user2 = User.objects.create(id='TEST002', name='Test2')

        # Create 2 intervals before the target interval and 1 interval after - total 4 intervals
        # Before intervals
        Interval.objects.create(
            start_date='2021-09-06', end_date='2021-09-19')
        Interval.objects.create(
            start_date='2021-09-20', end_date='2021-10-03')
        # Target interval
        target_interval = Interval.objects.create(
            start_date='2021-10-04', end_date='2021-10-17')
        # After interval
        Interval.objects.create(
            start_date='2021-10-18', end_date='2021-10-31')

        income_source0 = IncomeSource.objects.create(
            name='TestIncomeSource', user_id=user0.id)
        income_source1 = IncomeSource.objects.create(
            name='TestIncomeSource', user_id=user1.id)
        income_source2 = IncomeSource.objects.create(
            name='TestIncomeSource', user_id=user2.id)

        # User 1 has income in interval directly before target interval
        Income.objects.create(
            incomesource_id=income_source0.id, amount=2000, date='2021-09-23')
        # All other users have income in target interval
        Income.objects.create(
            incomesource_id=income_source0.id,
            amount=500,
            date='2021-10-07')
        Income.objects.create(
            incomesource_id=income_source1.id,
            amount=500,
            date='2021-10-07')
        Income.objects.create(
            incomesource_id=income_source2.id,
            amount=500,
            date='2021-10-07')
        return target_interval

    def test_with_all_user_incomes(self):
        target_interval = self.create_models()
        url = '/api/tax/' + str(target_interval.id)
        response = client.get(url, follow=True)
        self.assertEqual(
            response.data, {
                'TEST000': 1019, 'TEST001': 41, 'TEST002': 41})


class IncomePerInterval(TestCase):
    def create_models(self):
        user0 = User.objects.create(id='TEST000', name='Test0')
        user1 = User.objects.create(id='TEST001', name='Test1')
        user2 = User.objects.create(id='TEST002', name='Test2')

        target_interval = Interval.objects.create(
            start_date='2021-10-04', end_date='2021-10-17')
        Interval.objects.create(
            start_date='2021-09-20', end_date='2021-10-03')

        income_source0 = IncomeSource.objects.create(
            name='TestIncomeSource', user_id=user0.id)
        income_source1 = IncomeSource.objects.create(
            name='TestIncomeSource', user_id=user1.id)
        income_source2 = IncomeSource.objects.create(
            name='TestIncomeSource', user_id=user2.id)
        income_source3 = IncomeSource.objects.create(
            name='AnotherIncomeSource', user_id=user2.id)

        Income.objects.create(
            incomesource_id=income_source0.id,
            amount=500,
            date='2021-10-07')
        Income.objects.create(
            incomesource_id=income_source0.id,
            amount=500,
            date='2021-10-07')
        Income.objects.create(
            incomesource_id=income_source1.id,
            amount=500,
            date='2021-10-07')
        Income.objects.create(
            incomesource_id=income_source2.id,
            amount=500,
            date='2021-10-07')

        Income.objects.create(
            incomesource_id=income_source3.id,
            amount=123,
            date='2021-10-07')
        return target_interval

    def test_when_all_users_have_income_in_interval(self):
        target_interval = self.create_models()
        response = client.get('/api/income/income-source/' +
                              str(target_interval.id), follow=True)
        self.assertEqual(
            response.data, {
                'TEST000': {
                    'TestIncomeSource': 1000}, 'TEST001': {
                    'TestIncomeSource': 500}, 'TEST002': {
                    'TestIncomeSource': 500, 'AnotherIncomeSource': 123}})


class IncomeAvgPerInterval(IncomePerInterval):
    def test_avg_income_per_interval_when_all_users_paid(self):
        target_interval = self.create_models()
        response = client.get('/api/income/averaged/' +
                              str(target_interval.id), follow=True)
        self.assertEqual(
            response.data, {
                'TEST000': 500, 'TEST001': 250, 'TEST002': 311})
