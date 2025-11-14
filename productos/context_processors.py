from productos.contexts import Carrito  # Importa la unificada

def carrito_context(request):
    return {'carrito': Carrito(request)}