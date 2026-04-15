from django.shortcuts import render

# cupones/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Cupon
from django.db import transaction # ¡Importante para la atomicidad!
from .serializers import CuponSerializer, UsoCuponSerializer

# ¡Importante! Importar la clase de permiso
from rest_framework.permissions import IsAuthenticated

class ConsultarCuponAPIView(APIView):
    """
    Consulta los detalles de un cupón por su código.
    GET /api/cupones/consultar/<str:codigo>/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, codigo):
        # Usamos get_object_or_404 para manejar automáticamente el caso de no encontrarlo.
        cupon = get_object_or_404(Cupon, codigo__iexact=codigo) # iexact para no ser sensible a may/min

        # Verificamos si el cupón es válido para su uso.
        if not cupon.is_active:
            return Response(
                {"error": "El cupón no es válido, ha expirado o se ha agotado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CuponSerializer(cupon)
        return Response(serializer.data)

class MarcarUsoCuponAPIView(APIView):
    """
    Marca un cupón como usado y registra el contexto de su uso.
    POST /api/cupones/usar/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Validar los datos de entrada del cuerpo de la petición
        serializer = UsoCuponSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Usamos una transacción para garantizar que ambas operaciones (actualizar y crear)
        # se completen con éxito. Si algo falla, todo se revierte.
        codigo_cupon = serializer.validated_data.pop('codigo')
        try:
            with transaction.atomic():
                # 2. Obtener y bloquear el cupón para evitar condiciones de carrera
                # 'select_for_update()' bloquea la fila hasta que la transacción termine.
                cupon = Cupon.objects.select_for_update().get(codigo__iexact=codigo_cupon)

                # 3. Re-verificar si el cupón sigue siendo válido
                if not cupon.is_active:
                    return Response(
                        {"error": "No se puede usar el cupón. No es válido, ha expirado o se ha agotado."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # 4. Incrementar el contador de usos
                cupon.usos_actuales += 1
                cupon.save(update_fields=['usos_actuales'])

                # 5. Crear el registro de uso con los datos validados y el contexto
                # El usuario que hace la llamada a la API está en 'request.user'
                serializer.save(cupon=cupon, usuario_api=request.user)

        except Cupon.DoesNotExist:
            return Response({"error": "El cupón no existe."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Capturar cualquier otro error inesperado durante la transacción
            return Response({"error": f"Ocurrió un error inesperado: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                "mensaje": f"Cupón '{cupon.codigo}' marcado como usado.",
                "datos_registrados": serializer.data
            },
            status=status.HTTP_200_OK
        )
