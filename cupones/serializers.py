# cupones/serializers.py

from rest_framework import serializers

from encuestas.models import Tienda
from .models import Cupon, UsoCupon

class CuponSerializer(serializers.ModelSerializer):
    # Incluimos la propiedad 'is_active' para que el API la devuelva.
    is_active = serializers.BooleanField(read_only=True)
    # Le decimos al serializer que trate el campo como una relación múltiple.
    categorias = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Cupon
        # Lista de campos que se mostrarán en el API
        fields = [
            'codigo', 'tipo', 'valor', 'categorias', 'minimo_compra', 
            'maximo_descuento', 'is_active', 'limite_usos', 'usos_actuales'
        ]


class UsoCuponSerializer(serializers.ModelSerializer):
    """
    Serializer para validar los datos adicionales al momento de usar un cupón.
    """
    codigo = serializers.CharField(write_only=True, required=True)
    # Usamos SlugRelatedField para buscar la tienda por un campo que no es el ID.
    tienda = serializers.SlugRelatedField(
        slug_field='id_efsystem',  # Le decimos que en el modelo Tienda, busque usando este campo.
        queryset=Tienda.objects.all(), # El conjunto de objetos donde debe buscar.
        required=True
    )
    class Meta:
        model = UsoCupon
        # Especificamos los campos que esperamos recibir en el cuerpo de la petición.
        fields = ['codigo', 'tienda', 'nro_referencia', 'monto_total', 'monto_descuento']



