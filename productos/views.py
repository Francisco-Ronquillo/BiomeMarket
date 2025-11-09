from django.shortcuts import render
from django.views.generic import TemplateView
class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
class CartView(TemplateView):
    template_name = 'carrito.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
class listaProductosView(TemplateView):
    template_name = 'listado_productos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context