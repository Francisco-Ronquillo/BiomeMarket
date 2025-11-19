from django.shortcuts import render,redirect
from django.views.generic import TemplateView,CreateView
from accounts.models import Usuario
from django.urls import reverse_lazy
from django.views import View
from accounts.forms import UsuarioForm
from BiomeMarket.utils import  *
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
