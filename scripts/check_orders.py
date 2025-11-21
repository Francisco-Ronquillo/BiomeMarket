import os
import django
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BiomeMarket.settings')
sys.path.insert(0, BASE_DIR)

django.setup()
from productos.models import Orden

print('Últimas órdenes (máx 10):')
for o in Orden.objects.order_by('-created_at')[:10]:
    usuario = getattr(o, 'usuario', None)
    email = getattr(usuario, 'email', None) if usuario else None
    print(f'Orden id={o.id} paypal_order_id={o.paypal_order_id} total={o.total} currency={o.currency} status={o.status} created_at={o.created_at} usuario_id={getattr(usuario, "id", None)} email={email}')
