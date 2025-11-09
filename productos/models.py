from django.db import models
from accounts.models import Usuario
from django.utils import timezone
class Categoria(models.Model):
    TIPOS = [
        ('acuicola', 'Acuícola'),
        ('pesquero', 'Pesquero'),
        ('ganadero', 'Ganadero'),
        ('vegetal', 'Vegetal'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPOS, unique=True)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='categorias/', null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categorías"

    def _str_(self):
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

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name='Usuario')
    fecha_venta = models.DateTimeField(default=timezone.now, verbose_name='Fecha de venta')
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Total')
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente', verbose_name='Estado')
    metodo_pago = models.CharField(max_length=50, verbose_name='Método de pago')
    direccion_envio = models.TextField(verbose_name='Dirección de envío')

    def __str__(self):
        return f'Venta {self.id} - {self.usuario.nombre}'

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