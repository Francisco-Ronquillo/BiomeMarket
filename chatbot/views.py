import json
import re
from django.http import JsonResponse, HttpResponseNotAllowed
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from productos.models import Producto
from productos.contexts import Carrito


@require_POST
def chat_api(request):
    """API simple para el chatbot.

    - Recibe JSON { message: '...' }
    - Responde JSON con distintos tipos:
      - { type: 'productos', productos: [...] }
      - { type: 'carrito', items: [...], total: 0.0 }
      - { type: 'texto', message: '...' }
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        payload = request.POST.dict()

    message = (payload.get('message') or '').strip()
    lc = message.lower()

    # Intent: listar / buscar productos
    if any(k in lc for k in ['buscar', 'tienes', 'mostrar', 'qué productos', 'qué tienes']):
        # extrae query simple
        q = re.sub(r'^(buscar|mostrar|tienes|qué tienes|qué productos)(.*)', r'\2', lc).strip()
        q = q or payload.get('q', '')
        qs = Producto.objects.filter(nombre__icontains=q)[:8] if q else Producto.objects.all()[:8]
        productos = []
        for p in qs:
            productos.append({
                'id': p.id,
                'nombre': p.nombre,
                'precio': str(p.precio),
                'stock': p.stock,
                'imagen': p.imagen.url if getattr(p, 'imagen') and p.imagen else ''
            })
        return JsonResponse({'type': 'productos', 'productos': productos})

    # Intent: ver carrito
    if 'carrito' in lc or 'mi carrito' in lc:
        carrito = Carrito(request)
        items = []
        for it in carrito.get_cart_items():
            items.append({
                'id': it['producto'].id,
                'nombre': it['producto'].nombre,
                'cantidad': it['cantidad'],
                'precio_unitario': it['precio_unitario'],
                'subtotal': it['subtotal']
            })
        return JsonResponse({'type': 'carrito', 'items': items, 'total': carrito.total_precio()})

    # Intent: agregar producto
    if any(k in lc for k in ['agregar', 'añadir', 'añade', 'pon']):
        # Intenta extraer un id numérico
        num = re.search(r'\d+', lc)
        producto = None
        cantidad = 1
        if num:
            pid = int(num.group())
            producto = Producto.objects.filter(id=pid).first()
        else:
            # buscar por nombre
            # toma las palabras tras palabra clave
            m = re.sub(r'^(agregar|añadir|añade|pon)\s*', '', lc).strip()
            qs = Producto.objects.filter(nombre__icontains=m)[:1]
            producto = qs.first() if qs.exists() else None

        # Si el usuario menciona cantidad explícita ("2 tomates")
        found_qty = re.search(r'(\d+)\s*(?:x|unidades|uds|kg|kilos|kilo|cantidad)?', lc)
        if found_qty:
            try:
                cantidad = int(found_qty.group(1))
            except Exception:
                cantidad = 1

        if not producto:
              return JsonResponse({'type': 'texto', 'message': 'No pude identificar el producto a agregar. Puedes decir "agrega 2 tomates" o "agrega tomate".'})

        carrito = Carrito(request)
        try:
            nueva_cantidad = carrito.agregar(producto.id, cantidad)
            return JsonResponse({'type': 'texto', 'message': f'Agregado {producto.nombre} (cantidad añadida: {cantidad}). Total unidades en carrito: {carrito.total_items()}.', 'cart_total_items': carrito.total_items(), 'cart_total_price': carrito.total_precio()})
        except ValueError as e:
            return JsonResponse({'type': 'texto', 'message': str(e)})

    # Info general
    if any(k in lc for k in ['envío', 'envios', 'como funciona', 'horario', 'pago']):
        return JsonResponse({'type': 'texto', 'message': 'Para envíos y pagos revisa la sección "Cómo Funciona" en la página principal o contáctanos a través del formulario. También puedo ayudarte a buscar productos y administrar tu carrito.'})

    # Fallback
        return JsonResponse({'type': 'texto', 'message': 'No entendí. Puedo buscar productos, mostrar tu carrito o agregar productos. Prueba: "buscar tomate", "ver mi carrito" o "agregar tomate".'} )
