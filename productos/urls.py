from django.urls import path
from productos.views import *

app_name = 'productos'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('carrito/', CartView.as_view(), name='carrito'),
    path('listado_producto/', listaProductosView.as_view(), name='list_product'),
]