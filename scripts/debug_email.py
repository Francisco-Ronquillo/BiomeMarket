import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Forzar backend de consola para esta ejecución
os.environ['DJANGO_EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
# Ensure Django settings module
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
    parser.add_argument('orden_id', type=int, help='ID de la Orden a diagnosticar')
    args = parser.parse_args()

    print('===== CONFIGURACION DE EMAIL (efectiva) =====')
    print('EMAIL_BACKEND =', getattr(settings, 'EMAIL_BACKEND', '<not set>'))
    print('EMAIL_HOST =', getattr(settings, 'EMAIL_HOST', '<not set>'))
    print('EMAIL_PORT =', getattr(settings, 'EMAIL_PORT', '<not set>'))
    print('EMAIL_HOST_USER =', getattr(settings, 'EMAIL_HOST_USER', '<not set>'))
    pw = getattr(settings, 'EMAIL_HOST_PASSWORD', None)
    print('EMAIL_HOST_PASSWORD =', mask(pw))
    print('EMAIL_USE_TLS =', getattr(settings, 'EMAIL_USE_TLS', None))
    print('DEFAULT_FROM_EMAIL =', getattr(settings, 'DEFAULT_FROM_EMAIL', None))
    print()

    try:
        orden = Orden.objects.get(pk=args.orden_id)
    except Orden.DoesNotExist:
        print('Orden no encontrada')
        sys.exit(1)

    print('===== ORDEN =====')
    print('id=', orden.id)
    print('paypal_order_id=', orden.paypal_order_id)
    print('total=', orden.total, orden.currency)
    print('status=', orden.status)
    print('created_at=', orden.created_at)
    usuario = getattr(orden, 'usuario', None)
    if usuario:
        try:
            email = getattr(usuario, 'email', None)
            print('usuario_id=', usuario.id, 'email=', email)
        except Exception:
            print('usuario existe pero no se pudo leer email')
    else:
        print('usuario = None')

    print('\n===== ENVIANDO EMAIL A LA CONSOLA (simulado) =====')
    cart_items = []
    try:
        sent = _send_order_email(orden, cart_items, usuario_email=None)
        print('Funcion _send_order_email devolvio:', sent)
    except Exception as e:
        print('Error al ejecutar _send_order_email:', e)

    print('\nHecho.')
