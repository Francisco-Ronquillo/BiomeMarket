from django.shortcuts import render,redirect
from django.views.generic import TemplateView,CreateView
from accounts.models import Usuario
from django.urls import reverse_lazy
from django.views import View
from accounts.forms import UsuarioForm
from BiomeMarket.utils import  *
from django.core import signing
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
import hashlib
class LoginView(TemplateView):
    template_name = 'signIn.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    def post(self, request, *args, **kwargs):
        correo = request.POST.get('email')
        contraseña_plana = request.POST.get('password')
        contraseña_cifrada = hashlib.sha256(contraseña_plana.encode()).hexdigest()
        try:
            usuario = Usuario.objects.get(email=correo, contraseña=contraseña_cifrada)
            request.session['usuario_id'] = usuario.id
            return redirect('productos:home')
        except Usuario.DoesNotExist:
            context = self.get_context_data()
            context['error'] = 'Correo o contraseña incorrectos.'
            return self.render_to_response(context)
class SignupView(CreateView):
    template_name = 'signUp.html'
    form_class = UsuarioForm
    model = Usuario
    success_url = reverse_lazy('accounts:signin')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    def form_valid(self, form):
        contraseña_plana=self.request.POST.get('contraseña')
        contraseña_cifrada = hashlib.sha256(contraseña_plana.encode()).hexdigest()
        form.instance.contraseña = contraseña_cifrada
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class LogoutView(View):
    def get(self, request):
        request.session.flush()
        return redirect('productos:home')


class PasswordResetRequestView(TemplateView):
    template_name = 'password_reset.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        context = self.get_context_data()
        context['sent'] = False
        if not email:
            context['error'] = 'Por favor ingresa un correo.'
            return self.render_to_response(context)
        try:
            usuario = Usuario.objects.get(email=email)
            # generar token firmado con expiración manejada al validar
            token = signing.dumps({'user_id': usuario.id}, salt='password-reset')
            reset_path = reverse('accounts:password_reset_confirm', args=[token])
            reset_url = request.build_absolute_uri(reset_path)
            subject = 'Recuperar contraseña - BiomeMarket'
            text_body = f"Hola {getattr(usuario, 'nombre', '')},\n\nSigue este enlace para restablecer tu contraseña:\n{reset_url}\n\nSi no pediste este cambio, ignora este correo."
            # enviar correo (si falla, no mostrar detalles al usuario)
            try:
                msg = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [email])
                msg.send(fail_silently=True)
            except Exception:
                pass
        except Usuario.DoesNotExist:
            # Para evitar enumeración de usuarios, no indicamos error
            pass
        context['sent'] = True
        return self.render_to_response(context)


class PasswordResetConfirmView(TemplateView):
    template_name = 'password_reset_confirm.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs.get('token') or self.kwargs.get('token')
        context['valid'] = False
        try:
            data = signing.loads(token, salt='password-reset', max_age=60*60*24)  # 24 horas
            user_id = data.get('user_id')
            usuario = Usuario.objects.get(id=user_id)
            context['valid'] = True
            context['usuario_email'] = usuario.email
            context['token'] = token
        except Exception:
            context['error'] = 'El enlace no es válido o ha expirado.'
        return context

    def post(self, request, *args, **kwargs):
        token = kwargs.get('token')
        context = self.get_context_data(**kwargs)
        if not context.get('valid'):
            return self.render_to_response(context)
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if not password or not password2:
            context['error'] = 'Por favor completa ambos campos.'
            return self.render_to_response(context)
        if password != password2:
            context['error'] = 'Las contraseñas no coinciden.'
            return self.render_to_response(context)
        # establecer nueva contraseña
        try:
            data = signing.loads(token, salt='password-reset', max_age=60*60*24)
            usuario = Usuario.objects.get(id=data.get('user_id'))
            contraseña_cifrada = hashlib.sha256(password.encode()).hexdigest()
            usuario.contraseña = contraseña_cifrada
            usuario.save()
            context['success'] = 'Contraseña actualizada. Ahora puedes iniciar sesión.'
            return redirect('accounts:signin')
        except Exception:
            context['error'] = 'No fue posible actualizar la contraseña. Intenta nuevamente.'
            return self.render_to_response(context)
