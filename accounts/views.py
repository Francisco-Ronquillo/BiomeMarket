from django.shortcuts import render
from django.views.generic import TemplateView

class LoginView(TemplateView):
    template_name = 'signIn.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
class SignupView(TemplateView):
    template_name = 'signUp.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context