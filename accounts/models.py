from django.db import models
from django.utils import timezone

class Usuario(models.Model):
    nombre = models.CharField(max_length=100,verbose_name="Nombres",null=True,blank=True)
    apellido = models.CharField(max_length=100,verbose_name="Apellidos",null=True,blank=True)
    email = models.EmailField(max_length=150,unique=True,verbose_name="Correo Electrónico",null=True,blank=True)
    contraseña = models.CharField(max_length=64,verbose_name="Contraseña",null=True,blank=True)
    telefono = models.CharField(max_length=10,verbose_name="Telefono",null=True,blank=True)
    direccion = models.CharField(verbose_name="Dirección",null=True,blank=True)
    provincia = models.CharField(max_length=100,verbose_name="Provincia",null=True,blank=True)
    ciudad = models.CharField(max_length=100,verbose_name="Ciudad",null=True,blank=True)
    fecha_registro = models.DateField(default=timezone.now,verbose_name="Fecha de registro")
    activo = models.BooleanField(default=True,verbose_name="Activo")
    def __str__(self):
        return self.nombre
    def nombre_completo(self):
        return f"{self.nombre} {self.apellido}"