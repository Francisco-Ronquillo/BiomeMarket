from django.db import models
from django.utils import timezone

class Usuario(models.Model):
    nombre = models.CharField(max_length=100,verbose_name="Nombres")
    apellido = models.CharField(max_length=100,verbose_name="Apellidos")
    email = models.EmailField(max_length=150,unique=True,verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=10,verbose_name="Telefono")
    direccion = models.CharField(verbose_name="Dirección")
    fecha_registro = models.DateField(default=timezone.now,verbose_name="Fecha de registro")
    activo = models.BooleanField(default=True,verbose_name="Activo")
    def __str__(self):
        return self.nombre
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"