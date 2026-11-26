from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from .forms import (RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm,
                    ExpenseForm, IncomeForm, BudgetForm, ProfileForm, ChangePinForm)
from .models import Profile, Expense, Income, Budget, CATEGORY_CHOICES
from .utils import month_summary
import csv
from io import BytesIO
from xml.sax.saxutils import escape

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
MAX_ATTEMPTS = 5
LOCK_MINUTES = 15


# ---------------- AUTHENTICATION ----------------

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user = User.objects.create_user(username=d['username'], password=d['password'])
            profile = Profile(user=user, name=d['name'], age=d['age'], dob=d['dob'])
            profile.set_pin(d['pin'])
            profile.save()
            messages.success(request, 'Registration successful!')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'tracker/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'Logout')
    return redirect('login')


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            pin = form.cleaned_data['pin']
            profile = Profile.objects.filter(user__username=username).first()

            if profile and profile.is_locked():
                remaining = profile.locked_until - timezone.now()
                mins = int(remaining.total_seconds() // 60) + 1
                messages.error(request, f'Too many wrong attempts. Try again after {mins} minute(s).')
            elif profile and profile.check_pin(pin):
                profile.failed_attempts = 0
                profile.locked_until = None
                profile.save()
                request.session['reset_user_id'] = profile.user.id
                return redirect('reset_password')
            else:
                if profile:
                    profile.failed_attempts += 1
                    if profile.failed_attempts >= MAX_ATTEMPTS:
                        profile.locked_until = timezone.now() + timedelta(minutes=LOCK_MINUTES)
                        profile.failed_attempts = 0
                    profile.save()
                messages.error(request, 'Invalid username or PIN.')
    else:
        form = ForgotPasswordForm()
    return render(request, 'tracker/forgot_password.html', {'form': form})


def reset_password_view(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'username and PIN not verify')
        return redirect('forgot_password')

    user = User.objects.filter(pk=user_id).first()
    if user is None:
        request.session.pop('reset_user_id', None)
        return redirect('forgot_password')

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            request.session.pop('reset_user_id', None)
            messages.success(request, 'Password updated ,Try login again.')
            return redirect('login')
    else:
        form = ResetPasswordForm()
    return render(request, 'tracker/reset_password.html', {'form': form, 'reset_user': user})


# ---------------- DASHBOARD (temporary, Phase 4 me poora hoga) ----------------

@login_required
def dashboard(request):
    today = date.today()
    data = month_summary(request.user, today.year, today.month)

    context = {
        'month_name': today.strftime('%B %Y'),
        'total_expense': data['total_expense'],
        'total_income': data['total_income'],
        'balance': data['balance'],
        'expense_count': data['expenses'].count(),
        'recent_expenses': Expense.objects.filter(user=request.user)[:5],
        'categories': data['categories'],
        'budget': data['budget'],
        'percent': data['percent'],
        'bar_percent': data['bar_percent'],
        'bar_color': data['bar_color'],
        'over_budget': data['over_budget'],
        'remaining': data['remaining'],
    }
    return render(request, 'tracker/dashboard.html', context)

# ---------------- EXPENSE ----------------

def _safe_date(value):
    try:
        return parse_date(value) if value else None
    except ValueError:
        return None


@login_required
def _filter_expenses(request):
    """Search/filter logic: list page aur export dono yahi use karte hain"""
    expenses = Expense.objects.filter(user=request.user)

    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    month = request.GET.get('month', '')          # format: YYYY-MM
    date_from = _safe_date(request.GET.get('date_from'))
    date_to = _safe_date(request.GET.get('date_to'))

    if q:
        expenses = expenses.filter(note__icontains=q)
    if category:
        expenses = expenses.filter(category=category)
    if month:
        try:
            y, m = month.split('-')
            expenses = expenses.filter(date__year=int(y), date__month=int(m))
        except ValueError:
            pass
    if date_from:
        expenses = expenses.filter(date__gte=date_from)
    if date_to:
        expenses = expenses.filter(date__lte=date_to)

    filters = {
        'q': q, 'category': category, 'month': month,
        'date_from': request.GET.get('date_from', ''),
        'date_to': request.GET.get('date_to', ''),
    }
    return expenses, filters


@login_required
def expense_list(request):
    expenses, filters = _filter_expenses(request)
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'tracker/expense_list.html', {
        'expenses': expenses,
        'total': total,
        'categories': CATEGORY_CHOICES,
        'filters': filters,
    })

@login_required
def expense_add(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            messages.success(request, 'Expense added')
            return redirect('expense_list')
    else:
        form = ExpenseForm(initial={'date': date.today()})
    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Add Expense'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'tracker/expense_form.html', {'form': form, 'title': 'Edit Expense'})


@login_required
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    messages.success(request, 'Expense deleted')
    return redirect('expense_list')


# ---------------- INCOME ----------------

@login_required
def income_list(request):
    incomes = Income.objects.filter(user=request.user)
    total = incomes.aggregate(total=Sum('amount'))['total'] or 0
    return render(request, 'tracker/income_list.html', {'incomes': incomes, 'total': total})


@login_required
def income_add(request):
    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.user = request.user
            income.save()
            messages.success(request, 'Income added successfully.')
            return redirect('income_list')
    else:
        form = IncomeForm(initial={'date': date.today()})
    return render(request, 'tracker/income_form.html', {'form': form, 'title': 'Add Income'})


@login_required
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, 'Income updated successfully.')
            return redirect('income_list')
    else:
        form = IncomeForm(instance=income)
    return render(request, 'tracker/income_form.html', {'form': form, 'title': 'Edit Income'})


@login_required
@require_POST
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk, user=request.user)
    income.delete()
    messages.success(request, 'Income deleted successfully.')
    return redirect('income_list')

# ---------------- REPORTS (CHARTS) ----------------

@login_required
def reports(request):
    today = date.today()
    month_value = request.GET.get('month', '')
    try:
        y, m = (int(x) for x in month_value.split('-'))
        date(y, m, 1)
    except ValueError:
        y, m = today.year, today.month

    # Pie chart: category-wise expense for the selected month
    cat_rows = (Expense.objects
                .filter(user=request.user, date__year=y, date__month=m)
                .values('category')
                .annotate(total=Sum('amount'))
                .order_by('-total'))
    pie_labels = [r['category'] for r in cat_rows]
    pie_values = [float(r['total']) for r in cat_rows]

    # Bar chart: month-wise expense and income for the selected year
    monthly_expense = [0] * 12
    monthly_income = [0] * 12

    exp_rows = (Expense.objects.filter(user=request.user, date__year=y)
                .annotate(mon=ExtractMonth('date')).values('mon')
                .annotate(total=Sum('amount')).order_by())
    for r in exp_rows:
        monthly_expense[r['mon'] - 1] = float(r['total'])

    inc_rows = (Income.objects.filter(user=request.user, date__year=y)
                .annotate(mon=ExtractMonth('date')).values('mon')
                .annotate(total=Sum('amount')).order_by())
    for r in inc_rows:
        monthly_income[r['mon'] - 1] = float(r['total'])

    chart_data = {
        'pie_labels': pie_labels,
        'pie_values': pie_values,
        'bar_expense': monthly_expense,
        'bar_income': monthly_income,
        'year': y,
    }

    return render(request, 'tracker/reports.html', {
        'chart_data': chart_data,
        'selected_month': f'{y}-{m:02d}',
        'month_label': date(y, m, 1).strftime('%B %Y'),
        'year': y,
        'has_pie': len(pie_values) > 0,
        'month_total': sum(pie_values),
    })


# ---------------- BUDGET ----------------

@login_required
def budget_view(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            month_date = form.cleaned_data['month']
            Budget.objects.update_or_create(
                user=request.user,
                month=month_date.month,
                year=month_date.year,
                defaults={'amount': form.cleaned_data['amount']},
            )
            messages.success(request, 'Budget saved successfully.')
            return redirect('budget')
    else:
        form = BudgetForm(initial={'month': date.today().replace(day=1)})

    rows = []
    for b in Budget.objects.filter(user=request.user).order_by('-year', '-month'):
        spent = (Expense.objects
                 .filter(user=request.user, date__year=b.year, date__month=b.month)
                 .aggregate(t=Sum('amount'))['t'] or 0)
        percent = int(spent / b.amount * 100) if b.amount else 0
        if percent >= 100:
            color = 'danger'
        elif percent >= 70:
            color = 'warning'
        else:
            color = 'success'
        rows.append({
            'pk': b.pk,
            'label': date(b.year, b.month, 1).strftime('%B %Y'),
            'amount': b.amount,
            'spent': spent,
            'percent': percent,
            'bar_percent': min(percent, 100),
            'color': color,
            'over': spent > b.amount,
        })

    return render(request, 'tracker/budget.html', {'form': form, 'rows': rows})


@login_required
@require_POST
def budget_delete(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    budget.delete()
    messages.success(request, 'Budget deleted successfully.')
    return redirect('budget')


# ---------------- PROFILE ----------------

@login_required
def profile_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        messages.error(request, 'No profile found for this account.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'tracker/profile.html', {'form': form, 'profile': profile})


@login_required
def change_pin(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        messages.error(request, 'No profile found for this account.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = ChangePinForm(profile, request.POST)
        if form.is_valid():
            profile.set_pin(form.cleaned_data['new_pin'])
            profile.save()
            messages.success(request, 'Security PIN changed successfully.')
            return redirect('profile')
    else:
        form = ChangePinForm(profile)
    return render(request, 'tracker/change_pin.html', {'form': form})

# ---------------- EXPORT ----------------

def _csv_safe(text):
    """Excel formula injection se bachne ke liye"""
    if text and text[0] in ('=', '+', '-', '@'):
        return "'" + text
    return text


@login_required
def export_expenses_csv(request):
    expenses, _ = _filter_expenses(request)
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="expenses.csv"'
    response.write('\ufeff')  # Excel me sahi encoding ke liye

    writer = csv.writer(response)
    writer.writerow(['Date', 'Category', 'Note', 'Amount (INR)'])
    for e in expenses:
        writer.writerow([e.date.strftime('%d-%m-%Y'), e.category, _csv_safe(e.note), e.amount])
    writer.writerow([])
    writer.writerow(['', '', 'Total', total])
    return response


@login_required
def export_expenses_pdf(request):
    expenses, _ = _filter_expenses(request)
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    profile = Profile.objects.filter(user=request.user).first()
    name = profile.name if profile else request.user.username

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36,
                            topMargin=36, bottomMargin=36, title='Expense Report')
    styles = getSampleStyleSheet()

    elements = [
        Paragraph('Expense Report', styles['Title']),
        Paragraph(f'User: {escape(name)} &nbsp;|&nbsp; Generated on: {date.today():%d %b %Y}',
                  styles['Normal']),
        Spacer(1, 14),
    ]

    cell_style = styles['BodyText']
    data = [['Date', 'Category', 'Note', 'Amount (Rs.)']]
    for e in expenses:
        data.append([
            e.date.strftime('%d %b %Y'),
            e.category,
            Paragraph(escape(e.note or '-'), cell_style),
            f'{e.amount:.2f}',
        ])
    data.append(['', '', 'Total', f'{total:.2f}'])

    table = Table(data, colWidths=[80, 90, 260, 90], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f1f5f9')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expense_report.pdf"'
    return response