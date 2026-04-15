from django.db import models
from django.conf import settings

# cupones/models.py

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class CategoriaCupon(models.Model):
    nombre = models.CharField(max_length=100, unique=True, help_text="Ej:Botellas, Fragancias, Esencias")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría de Cupón"
        verbose_name_plural = "Categorías de Cupones"

class Cupon(models.Model):
    # --- ENUMERACIONES (CHOICES) ---
    class Tipo(models.TextChoices):
        PORCENTAJE = 'PORCENTAJE', 'Porcentaje'
        MONTO = 'MONTO', 'Monto Fijo'

    class Estatus(models.TextChoices):
        ACTIVO = 'ACTIVO', 'Activo'
        INACTIVO = 'INACTIVO', 'Inactivo'
        VENCIDO = 'VENCIDO', 'Vencido'
        AGOTADO = 'AGOTADO', 'Agotado'

    # --- CAMPOS DEL MODELO ---
    codigo = models.CharField(max_length=50, unique=True, help_text="El código que el usuario ingresará.")
    estatus = models.CharField(max_length=10, choices=Estatus.choices, default=Estatus.ACTIVO)
    tipo = models.CharField(max_length=10, choices=Tipo.choices, default=Tipo.PORCENTAJE)
    valor = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Valor del descuento (ej: 15 para 15% o 50 para S/50.00)")
    categorias = models.ManyToManyField(
        CategoriaCupon, 
        related_name="cupones",
        blank=True,  # Permite que un cupón no tenga ninguna categoría asignada.
        verbose_name="Categorías aplicables"
    )
    
    inicio = models.DateTimeField(default=timezone.now, help_text="Fecha y hora desde la que el cupón es válido.")
    vencimiento = models.DateTimeField(help_text="Fecha y hora hasta la que el cupón es válido.")
    
    minimo_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Monto mínimo de compra", validators=[MinValueValidator(0.00)])
    maximo_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Descuento máximo aplicable", help_text="Solo aplica para cupones de tipo Porcentaje.")

    limite_usos = models.PositiveIntegerField(default=1, help_text="Número total de veces que este cupón puede ser usado.", verbose_name="Límite de usos")
    usos_actuales = models.PositiveIntegerField(default=0, editable=False, help_text="Cuántas veces se ha usado el cupón.")

    def __str__(self):
        return self.codigo

    @property
    def is_active(self):
        """
        Propiedad que verifica si un cupón está actualmente válido para ser usado.
        """
        now = timezone.now()
        if self.estatus != self.Estatus.ACTIVO:
            return False
        if self.inicio > now:
            return False
        if self.vencimiento < now:
            # Opcional: podrías tener un script que actualice el estado a VENCIDO diariamente.
            # self.estatus = self.Estatus.VENCIDO
            # self.save()
            return False
        if self.usos_actuales >= self.limite_usos:
            # Opcional: podrías actualizar el estado a AGOTADO.
            self.estatus = self.Estatus.AGOTADO
            self.save()
            return False
        return True

    def clean(self):
        # Validaciones personalizadas
        if self.inicio >= self.vencimiento:
            raise ValidationError("La fecha de inicio debe ser anterior a la fecha de vencimiento.")
        if self.tipo == self.Tipo.PORCENTAJE and not (0 < self.valor <= 100):
            raise ValidationError("Para tipo Porcentaje, el valor debe estar entre 1 y 100.")

    class Meta:
        verbose_name = "Cupón"
        verbose_name_plural = "Cupones"
        ordering = ['-inicio']


class UsoCupon(models.Model):
    """
    Registra cada uso individual de un cupón, guardando el contexto.
    """
    cupon = models.ForeignKey(Cupon, on_delete=models.CASCADE, related_name="usos")
    usuario_api = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        help_text="El usuario de la API que realizó la operación."
    )
    fecha_uso = models.DateTimeField(auto_now_add=True, help_text="Fecha y hora exactas del uso.")
    
    # --- CAMPOS PARA DATOS EXTERNOS ---
    # Estos campos guardarán la información que nos envíes desde la otra plataforma.
    tienda = models.ForeignKey(
        'encuestas.Tienda',     # Referencia como 'app.Modelo'
        on_delete=models.SET_NULL, # Si se borra una tienda, el registro de uso no se borra, solo se quita la relación.
        null=True,              # Necesario para que SET_NULL funcione.
        blank=True,             # El campo es opcional en los formularios.
        related_name="usos_cupones" # Permite hacer Tienda.usos_cupones.all()
    )
    nro_referencia = models.CharField(max_length=255, null=True, blank=True)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_descuento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Cupón {self.cupon.codigo} usado el {self.fecha_uso.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Registro de Uso de Cupón"
        verbose_name_plural = "Registros de Uso de Cupones"
        ordering = ['-fecha_uso']