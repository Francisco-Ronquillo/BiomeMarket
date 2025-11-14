from django.urls import path
from productos.views import *
from . import views

app_name = 'productos'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('carrito/', CartView.as_view(), name='carrito'),
    path('carrito/ajax/', CartAjaxView.as_view(), name='carrito_ajax'),
    path('listado_producto/', listaProductosView.as_view(), name='list_product'),
    path('detalle_producto/<int:pk>/', detalleProductoView.as_view(), name='detalle_producto'),
    path('checkOut/', checkOut.as_view(), name='checkout'),

]