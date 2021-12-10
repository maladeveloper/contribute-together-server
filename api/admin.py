from django.contrib import admin
from .models import User, IncomeSource, Income, Payment, Interval

# Register your models here.
admin.site.register(User)
admin.site.register(IncomeSource)
admin.site.register(Income)
admin.site.register(Payment)
admin.site.register(Interval)
