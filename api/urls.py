from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    # PATCH
    path('interval/<str:interval>/amount/', views.change_interval_amount),

    # POST
    path('income/', views.IncomeView.as_view()),
    path('payment/', views.PaymentView.as_view()),
    # GET
    path('intervals/', views.IntervalLatestListView.as_view()),
    path('users/', views.UserListView.as_view()),
    path('income-sources/<str:user>/', views.UserIncomeSourceListView.as_view()),
    # Specified by interval
    path('payment/<str:interval>/', views.IntervalPaymentsListView.as_view()),
    path('tax/<str:interval>/', views.tax),
    path('income/income-source/<str:interval>/', views.income_per_interval),
    path('income/averaged/<str:interval>', views.avg_income_per_interval),

]
