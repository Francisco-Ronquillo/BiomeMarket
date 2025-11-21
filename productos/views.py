# use Django's EmailMessage for sending HTML mails
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView,ListView,DetailView,CreateView,UpdateView,DeleteView
from django.utils.decorators import method_decorator
from productos.models import *
from productos.contexts import Carrito
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views import View
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.core.mail import EmailMessage, EmailMultiAlternatives
from decimal import Decimal
from productos.models import Producto, Categoria
from decimal import  Decimal
import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()

        # ✅ Agrega el carrito al contexto
        carrito = Carrito(self.request)
        context['carrito'] = {
            'total_items': carrito.total_items(),
            'total_precio': carrito.total_precio()
        }

        usuario_id = self.request.session.get('usuario_id')
        context['usuario_autenticado'] = usuario_id is not None

        if usuario_id:
            try:
                context['usuario'] = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                context['usuario_autenticado'] = False
        # Preparar datos para el widget/chatbot en JavaScript
        nombre_usuario = ''
        if context.get('usuario'):
            nombre_usuario = getattr(context['usuario'], 'nombre', '') or ''
        context['bm_user_data'] = {
            'authenticated': context['usuario_autenticado'],
            'name': nombre_usuario
        }
        # Productos destacados: por cantidad vendida (DetalleVenta.cantidad)
        try:
            from .models import Producto as ProductoModel
            # usar la relación inversa por defecto 'detalleventa' y reemplazar NULL por 0
            destacados_qs = ProductoModel.objects.annotate(
                total_vendido=Coalesce(Sum('detalleventa__cantidad'), 0)
            ).filter(total_vendido__gt=0).order_by('-total_vendido', '-fecha_creacion')
            # sólo mostrar productos que hayan vendido al menos 1 unidad
            context['productos_destacados'] = list(destacados_qs[:4])
        except Exception:
            context['productos_destacados'] = []
        return context
class CartView(TemplateView):
    template_name = 'carrito.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrito = Carrito(self.request)
        context['cart_items'] = carrito.get_cart_items()  # Lista con 'subtotal', etc.
        context['total_precio'] = float(carrito.total_precio())
        context['total_items'] = carrito.total_items()
        context['items_unicos'] = carrito.items_unicos()

        # ← FIX: Subtotal y Total (sin descuentos/envío por ahora)
        context['subtotal'] = context['total_precio']  # Subtotal = total_precio
        context['total'] = context['subtotal']  # Total = subtotal (agrega envío/descuentos después)

        # Para badges en template
        context['umbral_oferta'] = 10.0  # Ejemplo

        if not context['cart_items']:
            context['mensaje_vacio'] = "Tu carrito está vacío. ¡Agrega productos frescos!"

        return context

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class CartAjaxView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return JsonResponse({'error': 'Método no permitido'})

    def post(self, request):
        carrito = Carrito(request)
        action = request.POST.get('accion') or request.POST.get('action')
        producto_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad', 1))
        codigo = request.POST.get('codigo', '')

        response_data = {
            'success': False,
            'subtotal': float(carrito.total_precio()),
            'total': float(carrito.total_precio()),
            'items_unicos': carrito.items_unicos(),
            'total_items': carrito.total_items(),
        }

        try:
            if action == 'agregar':
                carrito.agregar(producto_id, cantidad)
                response_data['success'] = True
                response_data['message'] = f'¡{Producto.objects.get(id=producto_id).nombre} agregado!'
                response_data['prev_cantidad'] = 0
            elif action == 'actualizar':
                producto = get_object_or_404(Producto, id=producto_id)
                if cantidad > producto.stock:
                    response_data['error'] = f'Stock insuficiente: Máx {producto.stock} disponibles.'
                    response_data['prev_cantidad'] = carrito.get_item(producto_id).get('cantidad', 0)
                    return JsonResponse(response_data)
                carrito.actualizar_cantidad(producto_id, cantidad)
                response_data['success'] = True
                response_data['message'] = f'Cantidad actualizada a {cantidad}.'
                response_data['prev_cantidad'] = cantidad
            elif action == 'remover':
                carrito.remover(producto_id)
                response_data['success'] = True
                response_data['message'] = 'Producto removido del carrito.'
            elif action == 'promo':
                if codigo == 'BIOME10':
                    response_data['success'] = True
                    response_data['total'] = response_data['subtotal'] * 0.9
                    response_data['message'] = '¡10% de descuento aplicado!'
                else:
                    response_data['error'] = 'Código inválido o expirado.'
            else:
                response_data['error'] = 'Acción no válida.'

            response_data['subtotal'] = float(carrito.total_precio())
            response_data['total'] = response_data['subtotal']
            response_data['items_unicos'] = carrito.items_unicos()
            response_data['total_items'] = carrito.total_items()
        except ValueError as e:
            response_data['error'] = str(e)
        except Exception:
            response_data['error'] = 'Error interno del servidor.'

        return JsonResponse(response_data)
class listaProductosView(ListView):
    template_name = 'listado_productos.html'
    model = Producto
    context_object_name = 'productos'
    paginate_by = 6
    ordering = ['nombre']

    def get_queryset(self):
        qs = super().get_queryset().distinct()
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))

        categoria_str = self.request.GET.get('categoria', '')
        if categoria_str:
            tipos = [t.strip() for t in categoria_str.split(',') if t.strip()]
            if tipos:
                qs = qs.filter(categoria__tipo__in=tipos)

        precio_max_str = self.request.GET.get('precio_max', '100.00').replace(',', '.')
        try:
            precio_max = Decimal(precio_max_str)
            if precio_max > Decimal('100'):
                precio_max = Decimal('100')
            qs = qs.filter(precio__lte=precio_max)
        except (ValueError, TypeError):
            pass

        ordering = self.request.GET.get('ordering', 'nombre')
        valid = ['nombre', 'precio', '-precio', '-fecha_creacion', 'peso', '-peso']
        qs = qs.order_by(ordering if ordering in valid else 'nombre')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.annotate(product_count=Count('productos')).order_by('nombre')
        usuario_id = self.request.session.get('usuario_id')
        context['usuario_autenticado'] = bool(usuario_id)
        if usuario_id:
            try:
                context['usuario'] = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                context['usuario_autenticado'] = False
        categoria_str = self.request.GET.get('categoria', '')
        context['selected_categorias'] = [t.strip() for t in categoria_str.split(',') if t.strip()]
        avg_price = Producto.objects.aggregate(Avg('precio'))['precio__avg']
        try:
            base = Decimal(str(avg_price)) if avg_price else Decimal('5.00')
            context['umbral_oferta'] = float((base * Decimal('0.8')).quantize(Decimal('0.01')))
        except (ValueError, TypeError):
            context['umbral_oferta'] = 4.00
        avg_weight = Producto.objects.aggregate(Avg('peso'))['peso__avg']
        context['avg_peso'] = round(float(avg_weight), 2) if avg_weight else 1.00
        context['total_count'] = self.object_list.count()
        context['max_price_fijo'] = 100.00
        carrito = Carrito(self.request)
        context['carrito'] = {'total_items': carrito.total_items(), 'total_precio': carrito.total_precio()}
        # Lista para comprobar orgánicos correctamente
        context['organicos'] = ['vegetal', 'frutas']
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            page_obj = context.get('page_obj')
            try:
                html = render_to_string('productos_partial.html', context, request=self.request)
            except Exception as e:
                return JsonResponse({'error': f'Error renderizando partial: {e}'}, status=500)
            return JsonResponse({
                'html': html,
                'total_count': context.get('total_count', 0),
                'current_page': page_obj.number if page_obj else 1,
                'page_length': len(page_obj.object_list) if page_obj else 0,
                'has_next': page_obj.has_next() if page_obj else False,
                'has_previous': page_obj.has_previous() if page_obj else False
            })
        return super().render_to_response(context, **response_kwargs)

class detalleProductoView(DetailView):
    model = Producto
    template_name = 'producto.html'
    context_object_name = 'producto'
    pk_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ✅ Agrega el carrito al contexto
        carrito = Carrito(self.request)
        context['carrito'] = {
            'total_items': carrito.total_items(),
            'total_precio': carrito.total_precio()
        }

        # ✅ Usuario autenticado (para navbar)
        usuario_id = self.request.session.get('usuario_id')
        context['usuario_autenticado'] = usuario_id is not None
        if usuario_id:
            try:
                context['usuario'] = Usuario.objects.get(id=usuario_id)
            except Usuario.DoesNotExist:
                context['usuario_autenticado'] = False

        # Productos similares
        context['productos_similares'] = Producto.objects.filter(
            categoria=context['producto'].categoria
        ).exclude(id=context['producto'].id)[:4]

        # Stock disponible
        context['stock_disponible'] = context['producto'].stock > 0

        # Precio por kg
        if context['producto'].peso:
            context['precio_por_kg'] = context['producto'].precio / context['producto'].peso

        # ✅ Umbral de oferta (para badges)
        avg_price_result = Producto.objects.aggregate(Avg('precio'))
        avg_price = avg_price_result['precio__avg']
        if avg_price is None:
            avg_price = Decimal('5.00')
        context['umbral_oferta'] = float(round(Decimal(str(avg_price)) * Decimal('0.8'), 2))

        return context


class checkOut(TemplateView):
    template_name = 'checkout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # pasar client id y datos del carrito para mostrar resumen
        context['PAYPAL_CLIENT_ID'] = getattr(settings, 'PAYPAL_CLIENT_ID', '')
        context['PAYPAL_MODE'] = getattr(settings, 'PAYPAL_MODE', 'sandbox')
        carrito = Carrito(self.request)
        context['cart_items'] = carrito.get_cart_items()
        context['cart_total'] = carrito.total_precio()
        # Información de usuario para el checkout: si está autenticado, usar su email
        usuario_id = self.request.session.get('usuario_id')
        context['usuario_autenticado'] = bool(usuario_id)
        if usuario_id:
            try:
                context['usuario'] = Usuario.objects.get(id=usuario_id)
            except Exception:
                context['usuario'] = None
        else:
            context['usuario'] = None
        return context


def _paypal_api_base():
    mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')
    if mode == 'live':
        return 'https://api-m.paypal.com'
    return 'https://api-m.sandbox.paypal.com'



def _get_paypal_token():
    client = getattr(settings, 'PAYPAL_CLIENT_ID', None)
    secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', None)
    if not client or not secret:
        raise RuntimeError('PAYPAL_CLIENT_ID or PAYPAL_CLIENT_SECRET not configured')
    url = f"{_paypal_api_base()}/v1/oauth2/token"
    headers = {'Accept': 'application/json', 'Accept-Language': 'en_US'}
    r = requests.post(url, headers=headers, auth=(client, secret), data={'grant_type': 'client_credentials'}, timeout=15)
    r.raise_for_status()
    return r.json().get('access_token')


def _send_order_email(orden, cart_items, usuario_email=None, request=None):
    """Envía un email con la factura al usuario (si tiene email)."""
    try:
        # si no recibimos email explícito, intentar obtenerlo desde la orden.usuario
        if not usuario_email:
            try:
                if getattr(orden, 'usuario', None):
                    usuario_email = getattr(orden.usuario, 'email', None)
            except Exception:
                usuario_email = None
        if not usuario_email:
            # nada que hacer si no hay correo del usuario
            import logging
            logging.getLogger(__name__).warning('No se encontró email del usuario para orden %s', getattr(orden, 'paypal_order_id', ''))
            return False
        subject = f"Factura - Orden {orden.paypal_order_id}"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@biomarket.local')
        to = [usuario_email]

        context = {
            'orden': orden,
            'cart_items': cart_items,
            'site_name': getattr(settings, 'SITE_NAME', 'BiomeMarket')
        }

        text_body = render_to_string('emails/factura.txt', context)
        html_body = render_to_string('emails/factura.html', context)

        msg = EmailMultiAlternatives(subject, text_body, from_email, to)
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        # no bloquear el flujo por un fallo de correo; registrar opcionalmente
        import logging
        logging.getLogger(__name__).exception('Error enviando email de orden: %s', e)
        return False


class PayPalCreateOrder(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            carrito = Carrito(request)
            total = float(carrito.total_precio())
            # si el checkout fue hecho por invitado, capturamos su email y lo guardamos en sesión
            guest_email = request.POST.get('guest_email') or request.POST.get('email')
            if guest_email:
                request.session['guest_email'] = guest_email
            token = _get_paypal_token()
            url = f"{_paypal_api_base()}/v2/checkout/orders"
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            payload = {
                'intent': 'CAPTURE',
                'purchase_units': [
                    {
                        'amount': {
                            'currency_code': 'USD',
                            'value': f"{total:.2f}"
                        }
                    }
                ]
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # devolver el id de la orden al cliente
            return JsonResponse({'id': data.get('id'), 'data': data})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class PayPalRedirectView(View):
    """Crea la orden en PayPal y redirige al usuario a la url de aprobación (approve)."""
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            carrito = Carrito(request)
            total = float(carrito.total_precio())
            # si el checkout fue hecho por invitado, capturamos su email y lo guardamos en sesión
            guest_email = request.POST.get('guest_email') or request.POST.get('email')
            usuario_id = request.session.get('usuario_id')
            if guest_email and not usuario_id:
                request.session['guest_email'] = guest_email
            token = _get_paypal_token()
            url = f"{_paypal_api_base()}/v2/checkout/orders"
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            # build return/cancel urls
            return_url = request.build_absolute_uri(reverse('productos:paypal_return'))
            cancel_url = request.build_absolute_uri(reverse('productos:carrito'))
            payload = {
                'intent': 'CAPTURE',
                'purchase_units': [
                    {
                        'amount': {
                            'currency_code': 'USD',
                            'value': f"{total:.2f}"
                        }
                    }
                ],
                'application_context': {
                    'return_url': return_url,
                    'cancel_url': cancel_url
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # find approval link
            links = data.get('links', [])
            approve = None
            for l in links:
                if l.get('rel') == 'approve' or l.get('rel') == 'approval_url':
                    approve = l.get('href')
                    break
            if not approve:
                # try link with rel 'approve'
                for l in links:
                    if 'approve' in l.get('rel', ''):
                        approve = l.get('href'); break
            if not approve:
                return JsonResponse({'error': 'No approval link returned by PayPal', 'data': data}, status=500)
            # redirect user to approval
            return HttpResponseRedirect(approve)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class PayPalReturnView(View):
    """Endpoint al que PayPal redirige después de la aprobación. Captura la orden y crea la Orden local."""
    def get(self, request):
        try:
            # PayPal returns token param with order id (v2 uses token)
            order_id = request.GET.get('token') or request.GET.get('orderID') or request.GET.get('order')
            if not order_id:
                return JsonResponse({'error': 'order id not provided'}, status=400)
            token = _get_paypal_token()
            url = f"{_paypal_api_base()}/v2/checkout/orders/{order_id}/capture"
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            resp = requests.post(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # persistir orden: extraer monto desde captures si está disponible
            from .models import Orden
            amount = 0.0
            currency = 'USD'
            purchases = data.get('purchase_units', [])
            # En la respuesta de captura, el importe suele estar en purchase_units[].payments.captures[].amount
            try:
                for pu in purchases:
                    payments = pu.get('payments', {})
                    captures = payments.get('captures', [])
                    if captures:
                        cap = captures[0]
                        amt = cap.get('amount', {})
                        amount = float(amt.get('value', 0) or 0)
                        currency = amt.get('currency_code', currency) or currency
                        break
                # fallback antiguo: purchase_units[].amount
                if amount == 0.0 and purchases:
                    pu0 = purchases[0]
                    amt0 = pu0.get('amount', {})
                    amount = float(amt0.get('value', 0) or 0)
                    currency = amt0.get('currency_code', currency) or currency
            except Exception:
                # si falla la extracción, mantener valores por defecto
                amount = 0.0
                currency = 'USD'

            # Crear la orden local usando los valores extraídos
            orden = Orden(paypal_order_id=order_id, total=amount, currency=currency, status='CAPTURED', raw_response=data)
            carrito = Carrito(request)
            cart_items = carrito.get_cart_items()
            usuario_email = None
            usuario_obj = None
            usuario_id = request.session.get('usuario_id')

            if usuario_id:
                try:
                    from accounts.models import Usuario
                    usuario_obj = Usuario.objects.get(id=usuario_id)
                    usuario_email = getattr(usuario_obj, 'email', None)
                    orden.usuario = usuario_obj
                except Exception:
                    usuario_email = None

            # si no tenemos usuario, usar email de invitado guardado en sesión
            if not usuario_email:
                guest_email = request.session.pop('guest_email', None)
                if guest_email:
                    usuario_email = guest_email
                    orden.guest_email = guest_email

            orden.save()

            # Registrar la venta y los detalles usando los items del carrito
            try:
                from .models import Venta, DetalleVenta
                # crear venta (usuario puede ser None para invitados)
                venta = Venta.objects.create(
                    usuario=orden.usuario if getattr(orden, 'usuario', None) else None,
                    total=Decimal(str(orden.total)),
                    estado='Completada',
                    metodo_pago='PayPal',
                    direccion_envio=''
                )
                # crear detalles y decrementar stock
                for it in cart_items:
                    prod = it.get('producto')
                    cantidad = int(it.get('cantidad', 0))
                    precio_unitario = Decimal(str(it.get('precio_unitario', 0)))
                    subtotal = Decimal(str(it.get('subtotal', 0)))
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=prod,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal
                    )
                    try:
                        # decrementar stock de producto de forma segura
                        prod.stock = max(0, prod.stock - cantidad)
                        prod.save()
                    except Exception:
                        pass
            except Exception:
                # Si falla el registro de la venta, no bloqueamos el flujo principal
                import logging
                logging.getLogger(__name__).exception('Error registrando Venta para orden %s', orden.paypal_order_id)

            # intentar enviar email (no bloquear si falla)
            try:
                _send_order_email(orden, cart_items, usuario_email=usuario_email, request=request)
            except Exception:
                pass

            # limpiar carrito
            carrito.limpiar()
            # redirigir a la página de confirmación
            return HttpResponseRedirect(reverse('productos:orden_confirmada', args=[orden.id]))
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)





class PayPalCaptureOrder(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            body = json.loads(request.body.decode('utf-8') or '{}')
            order_id = body.get('orderID') or body.get('orderId')
            if not order_id:
                return JsonResponse({'error': 'orderID missing'}, status=400)
            token = _get_paypal_token()
            url = f"{_paypal_api_base()}/v2/checkout/orders/{order_id}/capture"
            headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'}
            resp = requests.post(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            # Guardar orden en DB: extraer amount desde captures
            from .models import Orden
            amount = 0.0
            currency = 'USD'
            purchases = data.get('purchase_units', [])
            try:
                for pu in purchases:
                    payments = pu.get('payments', {})
                    captures = payments.get('captures', [])
                    if captures:
                        cap = captures[0]
                        amt = cap.get('amount', {})
                        amount = float(amt.get('value', 0) or 0)
                        currency = amt.get('currency_code', currency) or currency
                        break
                if amount == 0.0 and purchases:
                    pu0 = purchases[0]
                    amt0 = pu0.get('amount', {})
                    amount = float(amt0.get('value', 0) or 0)
                    currency = amt0.get('currency_code', currency) or currency
            except Exception:
                amount = 0.0
                currency = 'USD'

            # Crear la orden local y persistir guest_email si existe
            orden = Orden(paypal_order_id=order_id, total=amount, currency=currency, status='CAPTURED', raw_response=data)
            orden.guest_email = request.session.pop('guest_email', None)

            # preparar y enviar factura por email (si hay usuario/email)
            carrito = Carrito(request)
            cart_items = carrito.get_cart_items()
            usuario_email = None
            usuario_id = request.session.get('usuario_id')
            if usuario_id:
                try:
                    from accounts.models import Usuario
                    usuario = Usuario.objects.get(id=usuario_id)
                    usuario_email = getattr(usuario, 'email', None)
                    orden.usuario = usuario
                except Exception:
                    usuario_email = None

            # si no hay usuario asociado, usar email guardado en la orden (guest_email)
            if not usuario_email:
                usuario_email = orden.guest_email

            # asegurar que la orden está persistida antes de usar su id o enviar correo
            try:
                orden.save()
            except Exception:
                pass

            # Registrar la venta y los detalles usando los items del carrito
            try:
                from .models import Venta, DetalleVenta
                venta = Venta.objects.create(
                    usuario=orden.usuario if getattr(orden, 'usuario', None) else None,
                    total=Decimal(str(orden.total)),
                    estado='Completada',
                    metodo_pago='PayPal',
                    direccion_envio=''
                )
                for it in cart_items:
                    prod = it.get('producto')
                    cantidad = int(it.get('cantidad', 0))
                    precio_unitario = Decimal(str(it.get('precio_unitario', 0)))
                    subtotal = Decimal(str(it.get('subtotal', 0)))
                    DetalleVenta.objects.create(
                        venta=venta,
                        producto=prod,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        subtotal=subtotal
                    )
                    try:
                        prod.stock = max(0, prod.stock - cantidad)
                        prod.save()
                    except Exception:
                        pass
            except Exception:
                import logging
                logging.getLogger(__name__).exception('Error registrando Venta para orden %s', orden.paypal_order_id)

            try:
                _send_order_email(orden, cart_items, usuario_email=usuario_email, request=request)
            except Exception:
                pass

            # Si la captura es exitosa, limpiar el carrito
            carrito.limpiar()
            return JsonResponse({'status': 'captured', 'data': data, 'orden_id': orden.id})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class OrdenConfirmView(TemplateView):
    template_name = 'orden_confirmada.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = kwargs.get('pk') or self.kwargs.get('pk')
        from .models import Orden
        try:
            orden = Orden.objects.get(pk=pk)
        except Orden.DoesNotExist:
            orden = None
        context['orden'] = orden
        return context
    
def enviar_correo_confirmacion_html(usuario, fecha_cita, hora_cita):
    asunto = "Confirmación de tu cita"
    html_mensaje = render_to_string(
        "correo_confirmacion.html",
        {"usuario": usuario, "fecha_cita": fecha_cita, "hora_cita": hora_cita},
    )
    correo = EmailMessage(
        asunto, html_mensaje, "correomasivo81@gmail.com", [usuario.email]
    )  # usuario.email es el correo del paciente
    correo.content_subtype = "html"
    correo.send()


class MisComprasView(TemplateView):
    template_name = 'mis_compras.html'

    def dispatch(self, request, *args, **kwargs):
        # Requerir login mediante la sesión personalizada
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return HttpResponseRedirect(reverse('accounts:signin'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario_id = self.request.session.get('usuario_id')
        context['usuario_autenticado'] = bool(usuario_id)
        try:
            usuario = None
            if usuario_id:
                from accounts.models import Usuario
                usuario = Usuario.objects.get(id=usuario_id)
                context['usuario'] = usuario
        except Exception:
            usuario = None

        # Obtener todas las ventas asociadas al usuario
        try:
            compras = Venta.objects.filter(usuario_id=usuario_id).order_by('-fecha_venta').prefetch_related('detalles__producto')
        except Exception:
            compras = []

        context['compras'] = compras
        return context