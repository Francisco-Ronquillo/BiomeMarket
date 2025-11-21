import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BiomeMarket.settings')
sys.path.insert(0, BASE_DIR)

import django
django.setup()
from django.conf import settings
from productos.models import Orden
from productos.views import _send_order_email

def mask(s):
    if not s:
        return '<empty>'
    if len(s) <= 4:
        return '*' * len(s)
    return s[0] + '*'*(len(s)-2) + s[-1]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('orden_id', type=int, help='ID de la Orden a probar')
    args = parser.parse_args()

    print('EMAIL_BACKEND =', getattr(settings, 'EMAIL_BACKEND', '<not set>'))
    print('EMAIL_HOST =', getattr(settings, 'EMAIL_HOST', '<not set>'))
    print('EMAIL_PORT =', getattr(settings, 'EMAIL_PORT', '<not set>'))
    print('EMAIL_HOST_USER =', getattr(settings, 'EMAIL_HOST_USER', '<not set>'))
    print('EMAIL_HOST_PASSWORD =', mask(getattr(settings, 'EMAIL_HOST_PASSWORD', None)))
    print('EMAIL_USE_TLS =', getattr(settings, 'EMAIL_USE_TLS', None))
    print('DEFAULT_FROM_EMAIL =', getattr(settings, 'DEFAULT_FROM_EMAIL', None))
    print('\nIntentando enviar factura por SMTP...')

    try:
        orden = Orden.objects.get(pk=args.orden_id)
    except Orden.DoesNotExist:
        print('Orden no encontrada')
        sys.exit(1)

    cart_items = []
    sent = _send_order_email(orden, cart_items, usuario_email=None)
    print('Resultado envio:', sent)
