"""
Vistas de cuentas de usuario.

SignUpView: registro de nuevos usuarios subclasificando la vista genérica
CreateView y usando el UserCreationForm incorporado de Django, tal como se
explica en la Unidad 2. Se usa reverse_lazy porque las URLs aún no están
cargadas cuando se importa el módulo.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.views.generic import CreateView


class SignUpView(CreateView):
    """Registro de nuevos usuarios (accounts/signup/)."""
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')  # tras registrarse, a iniciar sesión

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Estilo Bootstrap 5 en los campos del formulario de registro.
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form
