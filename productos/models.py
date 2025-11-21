from django.db import models
from accounts.models import Usuario
from django.utils import timezone
class Categoria(models.Model):
    TIPOS = [
        ('acuicola', 'Acuícola'),
        ('pesquero', 'Pesquero'),
        ('ganadero', 'Ganadero'),
        ('vegetal', 'Vegetal'),
        ('frutas', 'Frutas'),
        ('cereales', 'Cereales'),
        ('lacteos', 'Lácteos'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS )
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(verbose_name="Nombre", max_length=100)
    descripcion = models.TextField(verbose_name="Descripcion")
    precio = models.DecimalField(verbose_name="Precio", max_digits=10, decimal_places=2)
    stock = models.IntegerField(verbose_name="Stock",default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos', verbose_name='Categoría')
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True, verbose_name="Imagen")
    peso = models.DecimalField(verbose_name="Peso (kg)", max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_creacion = models.DateField(auto_now_add=True, verbose_name="Fecha de creación")
    def __str__(self):
        return self.nombre

class Venta(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('Completada', 'Completada'),
        ('Cancelada', 'Cancelada'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name='Usuario', null=True, blank=True)
    fecha_venta = models.DateTimeField(default=timezone.now, verbose_name='Fecha de venta')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente', verbose_name='Estado')
    metodo_pago = models.CharField(max_length=50, verbose_name='Método de pago')
    direccion_envio = models.TextField(verbose_name='Dirección de envío')

    def __str__(self):
        usuario_nombre = getattr(self.usuario, 'nombre', 'Invitado') if self.usuario else 'Invitado'
        return f'Venta {self.id} - {usuario_nombre}'

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles', verbose_name='Venta')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name='Producto')
    cantidad = models.IntegerField(verbose_name='Cantidad')
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Precio unitario')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Subtotal')

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.producto.nombre} x {self.cantidad}'


class Orden(models.Model):
    STATUS = [
        ('CREATED', 'Created'),
        ('CAPTURED', 'Captured'),
        ('FAILED', 'Failed')
    ]

    paypal_order_id = models.CharField(max_length=128, unique=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True, verbose_name='Email de invitado')
    total = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, default='USD')
    status = models.CharField(max_length=20, choices=STATUS, default='CREATED')
    raw_response = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Orden {self.paypal_order_id} - {self.status} - {self.total} {self.currency}'


class CouponUsage(models.Model):
    """Registra el uso de un cupón por usuario o por email de invitado."""
    codigo = models.CharField(max_length=50)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    guest_email = models.EmailField(null=True, blank=True)
    usado_en = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (('codigo', 'usuario'), ('codigo', 'guest_email'))

    def __str__(self):
        who = self.usuario.email if self.usuario else (self.guest_email or 'Anónimo')
        return f'Cupón {self.codigo} usado por {who} en {self.usado_en}'