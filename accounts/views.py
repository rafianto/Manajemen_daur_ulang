from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django import forms


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nama Pengguna',
            'autofocus': True
        }),
        label='Nama Pengguna'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Kata Sandi'
        }),
        label='Kata Sandi'
    )


class CustomLoginView(auth_views.LoginView):
    template_name = 'registration/login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True
