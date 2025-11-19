from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView,ListView,DetailView,CreateView,UpdateView,DeleteView
from django.utils.decorators import method_decorator
from productos.models import *
from productos.contexts import Carrito
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.views import View
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from decimal import Decimal
from productos.models import Producto, Categoria
from decimal import  Decimal


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
        return context