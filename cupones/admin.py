from django.contrib import admin
import string
import random
from datetime import datetime

# cupones/admin.py

from django.contrib import admin
from .models import Cupon, CategoriaCupon, UsoCupon


def generar_codigo_cupon(longitud=4, prefijo='CUPON'):
    """
    Genera un código de cupón único con un formato preestablecido.
    Ejemplo: CUPON-X4T7-2025
    """
    caracteres = string.ascii_uppercase + string.digits # Usará letras mayúsculas y números
    año_actual = datetime.now().strftime('%Y')
    
    while True:
        # Genera la parte aleatoria del código
        codigo_aleatorio = ''.join(random.choice(caracteres) for _ in range(longitud))
        
        # Construye el código completo
        nuevo_codigo = f"{prefijo}-{codigo_aleatorio}-{año_actual}"
        
        # Comprueba si el código ya existe en la base de datos para garantizar unicidad
        if not Cupon.objects.filter(codigo=nuevo_codigo).exists():
            return nuevo_codigo # Si no existe, devuelve el nuevo código




@admin.register(CategoriaCupon)
class CategoriaCuponAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

class UsoCuponInline(admin.TabularInline):
    model = UsoCupon
    # --- CAMBIO AQUÍ ---
    # Reemplazamos 'id_tienda' por 'tienda'.
    fields = ('fecha_uso', 'usuario_api', 'tienda', 'display_pais', 'nro_referencia', 'monto_total', 'monto_descuento')
    readonly_fields = fields
    extra = 0
    can_delete = False
    ordering = ('-fecha_uso',)

    # Este método obtiene el país a través de la tienda relacionada.
    def display_pais(self, obj):
        if obj.tienda and obj.tienda.pais:
            return obj.tienda.pais.nombre  # Asumiendo que el modelo Pais tiene un campo 'nombre'
        return "-" # Devuelve un guion si no hay tienda o la tienda no tiene país
    
    # Nombre que se mostrará en la columna del admin
    display_pais.short_description = 'País'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cupon)
class CuponAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'estatus', 'tipo', 'valor', 'display_categorias', 
        'vencimiento', 'limite_usos', 'usos_actuales',
    )
    list_filter = ('estatus', 'tipo', 'categorias', 'vencimiento')
    search_fields = ('codigo', 'categorias__nombre')
    
    def get_changeform_initial_data(self, request):
        """
        Pre-llena el campo 'codigo' con un valor generado al añadir un nuevo cupón.
        """
        initial = super().get_changeform_initial_data(request)
        initial['codigo'] = generar_codigo_cupon()
        return initial

    def get_readonly_fields(self, request, obj=None):
        """
        Hace que el campo 'codigo' sea de solo lectura al EDITAR un cupón existente,
        pero permite su edición al AÑADIR uno nuevo.
        """
        if obj: # obj is not None, so this is an existing object
            return self.readonly_fields + ('codigo',)
        return self.readonly_fields


    # Esto crea el widget de selección múltiple con checkboxes y buscador.
    filter_horizontal = ('categorias',)
    # -----------------------------

    # Organiza los campos en el formulario de edición
    fieldsets = (
        ('Información Principal', {
            'fields': ('codigo', 'categorias', 'estatus')
        }),
        ('Detalles del Descuento', {
            'fields': ('tipo', 'valor', 'minimo_compra', 'maximo_descuento')
        }),
        ('Validez y Límites', {
            'fields': ('inicio', 'vencimiento', 'limite_usos')
        }),
        ('Estado (Solo Lectura)', {
            'fields': ('usos_actuales',),
            'classes': ('collapse',), # Oculta por defecto
        }),
    )
    
    # Campos que no se pueden editar manualmente en el admin
    readonly_fields = ('usos_actuales',)
    inlines = [UsoCuponInline]

    # Método para mostrar las categorías en la lista de cupones
    def display_categorias(self, obj):
        return ", ".join([cat.nombre for cat in obj.categorias.all()])
    
    display_categorias.short_description = 'Categorías'

@admin.register(UsoCupon)
class UsoCuponAdmin(admin.ModelAdmin):
    # --- CORRECCIÓN AQUÍ: Reemplazamos 'id_pais' por nuestro método 'display_pais' ---
    list_display = ('cupon', 'fecha_uso', 'usuario_api', 'tienda', 'display_pais', 'nro_referencia')
    list_filter = ('fecha_uso', 'cupon__codigo', 'tienda')
    search_fields = ('cupon__codigo', 'nro_referencia', 'tienda__nombre')

    # Reutilizamos el mismo método para mostrar el país
    def display_pais(self, obj):
        if obj.tienda and obj.tienda.pais:
            return obj.tienda.pais.nombre
        return "-"
    
    display_pais.short_description = 'País'


