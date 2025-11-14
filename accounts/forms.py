from django import forms
from accounts.models import Usuario
import datetime

class UsuarioForm(forms.ModelForm):
    confirmar_contraseña = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña', 'id': 'confirmar_contraseña'})
    )
    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email', 'telefono', 'direccion','contraseña',]
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombres', 'id': 'nombre'}),
            'apellido': forms.TextInput(attrs={'placeholder': 'Apellidos', 'id': 'apellido'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Correo Electrónico', 'id': 'email'}),
            'telefono': forms.TextInput(attrs={'placeholder': 'Teléfono', 'id': 'telefono'}),
            'direccion': forms.TextInput(attrs={'placeholder': 'Dirección', 'id': 'direccion'}),
            'contraseña': forms.PasswordInput(attrs={'placeholder': 'Contraseña', 'id': 'contraseña'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if not telefono.isdigit() or len(telefono) != 10:
            raise forms.ValidationError("El teléfono debe contener exactamente 10 dígitos.")
        return telefono

    def clean_nombres(self):
        nombres = self.cleaned_data.get('nombres')
        if not nombres:
            raise forms.ValidationError("Este campo es obligatorio.")
        if not nombres.replace(' ', '').isalpha():
            raise forms.ValidationError("El nombre solo debe contener letras y espacios.")
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos')
        if not apellidos:
            raise forms.ValidationError("Este campo es obligatorio.")
        if not apellidos.replace(' ', '').isalpha():
            raise forms.ValidationError("El apellido solo debe contener letras y espacios.")
        return apellidos