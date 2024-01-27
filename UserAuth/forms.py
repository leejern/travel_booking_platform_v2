from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Profile

class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', "placeholder": "full name"}))
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', "placeholder": "username"}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'class': 'form-control', "placeholder": "email"}))
    phone = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', "placeholder": "phone number"}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', "placeholder": "password"}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', "placeholder": "confirm Password"}))
    class Meta:
        model = User
        fields = ['full_name','username','email','phone','password1','password2']