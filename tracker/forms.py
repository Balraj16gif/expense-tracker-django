from datetime import date
from django import forms
from django.contrib.auth.models import User
from .models import Expense, Income, Profile


class BootstrapFormMixin:
    """All field need in Bootstrap class"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css)


def validate_pin(value):
    if not value.isdigit() or len(value) != 6:
        raise forms.ValidationError('PIN must be exactly 6 digits.')


def pin_widget():
    return forms.PasswordInput(attrs={
        'maxlength': 6,
        'inputmode': 'numeric',
        'class': 'form-control pin-input',
        'autocomplete': 'off',
    })


class RegisterForm(BootstrapFormMixin, forms.Form):
    name = forms.CharField(max_length=100, label='Full Name')
    age = forms.IntegerField(min_value=1, max_value=120)
    dob = forms.DateField(label='Date of Birth', widget=forms.DateInput(attrs={'type': 'date'}))
    username = forms.CharField(max_length=150)
    password = forms.CharField(min_length=4, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    pin = forms.CharField(label='Security PIN (6 digits)', max_length=6,
                          validators=[validate_pin], widget=pin_widget())
    confirm_pin = forms.CharField(label='Confirm PIN', max_length=6, widget=pin_widget())

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_dob(self):
        dob = self.cleaned_data['dob']
        if dob > date.today():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        return dob

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('confirm_password'):
            if cleaned['password'] != cleaned['confirm_password']:
                self.add_error('confirm_password', 'Passwords do not match.')
        if cleaned.get('pin') and cleaned.get('confirm_pin'):
            if cleaned['pin'] != cleaned['confirm_pin']:
                self.add_error('confirm_pin', 'PINs do not match.')
        return cleaned


class LoginForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)


class ForgotPasswordForm(BootstrapFormMixin, forms.Form):
    username = forms.CharField()
    pin = forms.CharField(label='Security PIN (6 digits)', max_length=6,
                          validators=[validate_pin], widget=pin_widget())


class ResetPasswordForm(BootstrapFormMixin, forms.Form):
    new_password = forms.CharField(min_length=4, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password') and cleaned.get('confirm_password'):
            if cleaned['new_password'] != cleaned['confirm_password']:
                self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned

class ExpenseForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'category', 'date', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'note': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        return amount


class IncomeForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Income
        fields = ['amount', 'source', 'date', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0.00'}),
            'source': forms.TextInput(attrs={'placeholder': 'e.g. Salary, Pocket Money'}),
            'date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'note': forms.TextInput(attrs={'placeholder': 'Optional note'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than 0.')
        return amount

class BudgetForm(BootstrapFormMixin, forms.Form):
    month = forms.DateField(
        label='Month',
        input_formats=['%Y-%m'],
        widget=forms.DateInput(attrs={'type': 'month'}, format='%Y-%m'),
    )
    amount = forms.DecimalField(
        label='Budget Amount (₹)',
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'e.g. 10000'}),
    )


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['name', 'age', 'dob']
        labels = {'name': 'Full Name', 'dob': 'Date of Birth'}
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }

    def clean_dob(self):
        dob = self.cleaned_data['dob']
        if dob > date.today():
            raise forms.ValidationError('Date of birth cannot be in the future.')
        return dob

    def clean_age(self):
        age = self.cleaned_data['age']
        if age < 1 or age > 120:
            raise forms.ValidationError('Enter a valid age.')
        return age


class ChangePinForm(BootstrapFormMixin, forms.Form):
    current_pin = forms.CharField(label='Current PIN', max_length=6,
                                  validators=[validate_pin], widget=pin_widget())
    new_pin = forms.CharField(label='New PIN (6 digits)', max_length=6,
                              validators=[validate_pin], widget=pin_widget())
    confirm_new_pin = forms.CharField(label='Confirm New PIN', max_length=6, widget=pin_widget())

    def __init__(self, profile, *args, **kwargs):
        self.profile = profile
        super().__init__(*args, **kwargs)

    def clean_current_pin(self):
        pin = self.cleaned_data['current_pin']
        if not self.profile.check_pin(pin):
            raise forms.ValidationError('Current PIN is incorrect.')
        return pin

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_pin') and cleaned.get('confirm_new_pin'):
            if cleaned['new_pin'] != cleaned['confirm_new_pin']:
                self.add_error('confirm_new_pin', 'PINs do not match.')
        return cleaned