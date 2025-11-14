from decimal import Decimal
from django.conf import settings
from .models import Producto

CART_SESSION_ID = getattr(settings, 'CART_SESSION_ID', 'biomarket_carrito')

class Carrito:
    def __init__(self, request):
        self.session = request.session
        self.request = request
        carrito_data = self.session.get(CART_SESSION_ID, {})
        if not isinstance(carrito_data, dict):
            carrito_data = {}
        self._limpiar_carrito(carrito_data)
        self.carrito = carrito_data

    def _limpiar_carrito(self, data):
        if isinstance(data, dict):
            for pid, item in list(data.items()):
                if isinstance(item, dict):
                    if 'precio_unitario' in item and isinstance(item['precio_unitario'], Decimal):
                        item['precio_unitario'] = float(item['precio_unitario'])
                    if 'peso' in item and isinstance(item['peso'], Decimal):
                        item['peso'] = float(item['peso'])
                    elif 'peso' in item and item['peso'] is None:
                        item['peso'] = None
                    if 'cantidad' in item and not isinstance(item['cantidad'], int):
                        item['cantidad'] = int(item['cantidad'])
                    if 'nombre' in item:
                        item['nombre'] = str(item['nombre'])
                    item.pop('producto', None)
                    item.pop('subtotal', None)
                else:
                    del data[pid]

    def agregar(self, product_id, cantidad=1):
        product_id = str(product_id)
        try:
            producto = Producto.objects.get(id=product_id)
        except Producto.DoesNotExist:
            raise ValueError("Producto no encontrado")

        if producto.stock <= 0:
            raise ValueError("Sin stock")

        if product_id not in self.carrito:
            peso_val = float(producto.peso) if producto.peso is not None else None
            self.carrito[product_id] = {
                'cantidad': 0,
                'precio_unitario': float(producto.precio),
                'nombre': str(producto.nombre),
                'peso': peso_val
            }

        stock_disponible = producto.stock - self.carrito[product_id]['cantidad']
        cantidad = min(cantidad, stock_disponible)
        if cantidad <= 0:
            raise ValueError("Stock insuficiente")

        self.carrito[product_id]['cantidad'] += cantidad
        if self.carrito[product_id]['cantidad'] <= 0:
            del self.carrito[product_id]
        self.guardar()
        return self.carrito.get(product_id, {}).get('cantidad', 0)

    def remover(self, product_id):
        product_id = str(product_id)
        if product_id in self.carrito:
            del self.carrito[product_id]
            self.guardar()

    def actualizar_cantidad(self, product_id, cantidad):
        product_id = str(product_id)
        try:
            producto = Producto.objects.get(id=product_id)
        except Producto.DoesNotExist:
            return

        if product_id in self.carrito:
            stock_disponible = producto.stock
            nueva_cantidad = max(int(cantidad), 0)
            if nueva_cantidad > stock_disponible:
                nueva_cantidad = stock_disponible
            if nueva_cantidad <= 0:
                del self.carrito[product_id]
            else:
                self.carrito[product_id]['cantidad'] = nueva_cantidad
            self.guardar()

    def limpiar(self):
        self.session[CART_SESSION_ID] = {}
        self.carrito = {}
        self.session.modified = True

    def get_item(self, product_id):
        item = self.carrito.get(str(product_id), {}).copy()
        if item:
            item['precio_unitario'] = float(item.get('precio_unitario', 0))
            if 'peso' in item:
                item['peso'] = float(item['peso']) if item['peso'] is not None else None
            item['precio_total'] = float(item['precio_unitario'] * item.get('cantidad', 0))
        return item

    def get_cart_items(self):
        if not self.carrito:
            return []

        product_ids = [int(pid) for pid in self.carrito.keys()]
        try:
            productos = Producto.objects.filter(id__in=product_ids)
            productos_dict = {p.id: p for p in productos}
        except:
            productos_dict = {}

        cart_items = []
        pids_to_remove = []
        for pid_str, data in self.carrito.items():
            pid = int(pid_str)
            if pid in productos_dict:
                producto = productos_dict[pid]
                precio_actual = float(producto.precio)
                subtotal = precio_actual * data['cantidad']
                peso_val = float(producto.peso) if producto.peso is not None else None
                disponible = producto.stock >= data['cantidad']
                if not disponible:
                    subtotal = precio_actual * producto.stock
                    pids_to_remove.append(pid_str)
                cart_items.append({
                    'producto': producto,
                    'cantidad': data['cantidad'],
                    'precio_unitario': precio_actual,
                    'subtotal': subtotal,
                    'disponible': disponible,
                    'peso': peso_val,
                    'nombre': data.get('nombre', producto.nombre)
                })
            else:
                pids_to_remove.append(pid_str)

        for pid in pids_to_remove:
            if pid in self.carrito:
                del self.carrito[pid]
        if pids_to_remove:
            self.guardar()

        return cart_items

    def __iter__(self):
        return iter(self.get_cart_items())

    def __len__(self):
        return sum(item['cantidad'] for item in self.get_cart_items())

    def total_items(self):
        return self.__len__()

    def total_precio(self):
        total = 0.0
        for item in self.get_cart_items():
            total += item['subtotal']
        return round(total, 2)

    def items_unicos(self):
        return len(self.get_cart_items())

    def guardar(self):
        self._limpiar_carrito(self.carrito)
        self.session[CART_SESSION_ID] = self.carrito
        self.session.modified = True

    def clear(self):
        self.limpiar()
