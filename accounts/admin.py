from django.contrib import admin
from accounts.models import *

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'apellido', 'email', 'telefono', 'activo')
    search_fields = ('nombre', 'apellido', 'email')
    list_filter = ('activo', 'fecha_registro')
    ordering = ('nombre', 'apellido')
    readonly_fields = ('fecha_registro',)
# Register your models here.
