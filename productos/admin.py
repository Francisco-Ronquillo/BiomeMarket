from django.contrib import admin
from productos.models import *
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'descripcion')
    search_fields = ('nombre', 'tipo')
    ordering = ('nombre',)
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'stock', 'categoria', 'fecha_creacion')
    search_fields = ('nombre', 'categoria__nombre')
    list_filter = ('categoria', 'fecha_creacion')
    ordering = ('nombre',)
    readonly_fields = ('fecha_creacion',)

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_venta', 'total', 'estado', 'metodo_pago')
    search_fields = ('usuario__nombre', 'estado', 'metodo_pago')
    list_filter = ('estado', 'fecha_venta')
    ordering = ('-fecha_venta',)
    readonly_fields = ('fecha_venta', 'total')
@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'producto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('venta__id', 'producto__nombre')
    ordering = ('venta',)
    readonly_fields = ('subtotal',)
# Register your models here.
