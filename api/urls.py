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
    path('payment/<str:interval>/', views.payment),
    path('tax/<str:interval>/', views.tax),
    path('income/income-source/<str:interval>/', views.income_per_interval),
    path('income/averaged/<str:interval>', views.avg_income_per_interval),
    path('users/unsubmitted/<str:interval>', views.unsubmitted_users_per_interval),
    # Metrics
    path('metrics/total-income', views.total_income),
    path('metrics/total-paid', views.total_paid),
    path('metrics/total-income-by-interval', views.total_income_by_interval),
    path('metrics/total-tax-by-interval', views.total_tax_by_interval),

    # DELETE
    path('income/<str:income>', views.delete_specific_income),

    # GET and PATCH
    path('numerical-params/', views.numerical_params),


]
