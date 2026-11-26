from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/export/csv/', views.export_expenses_csv, name='export_expenses_csv'),
    path('expenses/export/pdf/', views.export_expenses_pdf, name='export_expenses_pdf'),

    # Income
    path('income/', views.income_list, name='income_list'),
    path('income/add/', views.income_add, name='income_add'),
    path('income/<int:pk>/edit/', views.income_edit, name='income_edit'),
    path('income/<int:pk>/delete/', views.income_delete, name='income_delete'),
    # Reports
    path('reports/', views.reports, name='reports'),

    # Budget
    path('budget/', views.budget_view, name='budget'),
    path('budget/<int:pk>/delete/', views.budget_delete, name='budget_delete'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/change-pin/', views.change_pin, name='change_pin'),
]