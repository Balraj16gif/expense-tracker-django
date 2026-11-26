from decimal import Decimal
from django.db.models import Sum

from .models import Expense, Income, Budget


def month_summary(user, year, month):
    """whole month : expenses, income, balance, budget, category-wise data"""
    expenses = Expense.objects.filter(user=user, date__year=year, date__month=month)
    incomes = Income.objects.filter(user=user, date__year=year, date__month=month)

    total_expense = expenses.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    total_income = incomes.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    balance = total_income - total_expense

    budget_obj = Budget.objects.filter(user=user, year=year, month=month).first()
    budget = budget_obj.amount if budget_obj else None

    percent = 0
    over_budget = False
    bar_color = 'success'
    remaining = None
    if budget and budget > 0:
        percent = int(total_expense / budget * 100)
        over_budget = total_expense > budget
        remaining = budget - total_expense
        if percent >= 100:
            bar_color = 'danger'
        elif percent >= 70:
            bar_color = 'warning'

    categories = list(
        expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    )
    for c in categories:
        c['share'] = int(c['total'] / total_expense * 100) if total_expense else 0

    return {
        'expenses': expenses,
        'total_expense': total_expense,
        'total_income': total_income,
        'balance': balance,
        'budget': budget,
        'percent': percent,
        'bar_percent': min(percent, 100),
        'over_budget': over_budget,
        'bar_color': bar_color,
        'remaining': remaining,
        'categories': categories,
    }