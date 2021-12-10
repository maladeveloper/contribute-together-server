from django.db import models

# Create your models here.


class User(models.Model):
    id = models.CharField(max_length=7, primary_key=True)
    name = models.CharField(max_length=100)


class IncomeSource(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default='MAL0001')

    class Meta:
        unique_together = ('name', 'user')


class Interval(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.IntegerField(default=1100)


class Income(models.Model):
    incomesource = models.ForeignKey(IncomeSource, on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateField()


class Payment(models.Model):
    interval = models.ForeignKey(Interval, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.IntegerField()
