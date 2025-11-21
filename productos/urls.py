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
    # PayPal integration endpoints
    path('paypal/create-order/', PayPalCreateOrder.as_view(), name='paypal_create_order'),
    path('paypal/capture-order/', PayPalCaptureOrder.as_view(), name='paypal_capture_order'),
    path('paypal/redirect/', PayPalRedirectView.as_view(), name='paypal_redirect'),
    path('paypal/return/', PayPalReturnView.as_view(), name='paypal_return'),
    path('orden/confirmada/<int:pk>/', OrdenConfirmView.as_view(), name='orden_confirmada'),
    path('mis_compras/', MisComprasView.as_view(), name='mis_compras'),

]