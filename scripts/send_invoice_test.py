import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BiomeMarket.settings')
# Forzar backend de consola para que el email aparezca en stdout
os.environ['DJANGO_EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
sys.path.insert(0, BASE_DIR)

import django
django.setup()

from productos.models import Orden
from productos.views import _send_order_email

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('orden_id', type=int, help='ID de la Orden a probar')
    args = parser.parse_args()

    try:
        orden = Orden.objects.get(pk=args.orden_id)
    except Orden.DoesNotExist:
        print('Orden no encontrada')
        sys.exit(1)

    # Intentar reconstruir elementos del carrito desde raw_response si es posible
    cart_items = []
    try:
        data = orden.raw_response or {}
        purchases = data.get('purchase_units', [])
        for pu in purchases:
            items = pu.get('items', [])
            for it in items:
                # construir estructura mínima esperada por la plantilla
                cart_items.append({
                    'producto': type('P', (), {'nombre': it.get('name', 'Item')}),
                    'cantidad': int(it.get('quantity', 1)),
                    'subtotal': it.get('unit_amount', {}).get('value') if it.get('unit_amount') else None,
                    'precio_unitario': it.get('unit_amount', {}).get('value') if it.get('unit_amount') else None,
                })
    except Exception:
        cart_items = []

    print(f'Enviando email de prueba para orden {orden.id} (paypal_order_id={orden.paypal_order_id})...')
    sent = _send_order_email(orden, cart_items, usuario_email=None)
    print('Resultado envio:', sent)
