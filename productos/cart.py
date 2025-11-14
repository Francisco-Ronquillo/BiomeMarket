from decimal import Decimal
from django.conf import settings
from productos.models import Producto


class Cart:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        cart_data = self.session.get(settings.CART_SESSION_ID, {})
        if not isinstance(cart_data, dict):
            cart_data = {}
        # Limpia residuos no serializables (defensivo)
        self._limpiar_cart(cart_data)
        self.cart = cart_data

    def _limpiar_cart(self, data):
        """Convierte Decimales a float y remueve objetos no serializables."""
        if isinstance(data, dict):
            for pid, item in list(data.items()):
                if isinstance(item, dict):
                    if 'precio_unit' in item and isinstance(item['precio_unit'], Decimal):
                        item['precio_unit'] = float(item['precio_unit'])
                    # Remueve keys runtime (e.g., si se coló 'producto')
                    item.pop('producto', None)
                    item.pop('subtotal', None)  # Calculado, no persistir
                else:
                    # Si item no es dict válido, remueve
                    del data[pid]

    def add(self, product_id, quantity=1, update_quantity=False):
        product_id = str(product_id)
        from .models import Producto  # Lazy import
        try:
            producto = Producto.objects.get(id=product_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")

        if product_id not in self.cart:
            self.cart[product_id] = {
                'precio_unit': float(producto.precio),  # ← Siempre float, evita Decimal
                'cantidad': 0
            }

        if update_quantity:
            self.cart[product_id]['cantidad'] = self.cart[product_id]['cantidad'] + quantity
        else:
            self.cart[product_id]['cantidad'] += quantity

        # Limpia si cantidad <=0
        if self.cart[product_id]['cantidad'] <= 0:
            del self.cart[product_id]

        self.save()
        return self.cart[product_id]['cantidad'] if product_id in self.cart else 0

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def update_quantity(self, product_id, quantity):
        product_id = str(product_id)
        if product_id in self.cart:
            self.cart[product_id]['cantidad'] = max(int(quantity), 0)
            if self.cart[product_id]['cantidad'] == 0:
                self.remove(product_id)
            else:
                self.save()

    def get_cart_items(self):
        """Para views/templates: Rebuild lista con objetos Producto (NO modifica self.cart)."""
        if not self.cart:
            return []

        product_ids = [int(pid) for pid in self.cart.keys()]
        try:
            productos = Producto.objects.filter(id__in=product_ids)
            productos_dict = {p.id: p for p in productos}
        except Exception:
            productos_dict = {}  # Fallback si error DB

        cart_items = []
        pids_to_remove = []
        for product_id, item in self.cart.items():
            pid = int(product_id)
            if pid in productos_dict:
                producto = productos_dict[pid]
                subtotal = float(item['precio_unit']) * item['cantidad']  # ← float explícito
                cart_items.append({
                    'producto': producto,
                    'cantidad': item['cantidad'],
                    'precio_unit': float(item['precio_unit']),
                    'subtotal': subtotal
                })
            else:
                # Producto eliminado: remueve de cart
                pids_to_remove.append(product_id)

        # Limpia inválidos
        for pid in pids_to_remove:
            del self.cart[pid]
        if pids_to_remove:
            self.save()

        return cart_items

    def __iter__(self):
        """Itera sin modificar self.cart (usa get_cart_items)."""
        return iter(self.get_cart_items())

    def __len__(self):
        """Total unidades (usa get_cart_items para consistencia)."""
        return sum(item['cantidad'] for item in self.get_cart_items())

    def total_items(self):
        return len(self)

    def subtotal(self):
        """Subtotal (float seguro)."""
        total = 0.0
        for item in self.get_cart_items():
            total += item['subtotal']
        return round(total, 2)

    def total(self):
        return self.subtotal()  # + envío/descuento si expandes

    def save(self):
        """Guarda solo primitivos en sesión."""
        self._limpiar_cart(self.cart)  # Asegura serializable
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.cart = {}
        self.session.modified = True