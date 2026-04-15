from django.http import JsonResponse
from django.urls import reverse
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
#import logging
import secrets
from encuestas.models import TicketConsulta, Tienda, EncuestaFija
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.permissions import IsAuthenticated
#from logger.utils.logger import Logger

#logger = logging.getLogger('encuestas')

# Vista para obtener el JWT
class MyTokenObtainPairView(TokenObtainPairView):
    pass  # Aquí puedes personalizar el comportamiento si lo deseas

    
    
# Vista para refrescar el JWT
class MyTokenRefreshView(TokenRefreshView):
    pass  # Aquí también puedes personalizar si es necesario



class EncuestaTiendaAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
 #       logger.debug(f"POST /api/encuesta-tienda/ payload: {request.data}")
        # Extraer parámetros del cuerpo del request
        tienda_id = request.data.get("tienda_id")
        codigo = request.data.get("codigo")
        monto = request.data.get("monto")

  #      logger.debug(f"Parametros extraídos: tienda_id={tienda_id}, codigo={codigo}, monto={monto}")

#        Logger.add_to_log("info", f"Solicitud POST a EncuestaTiendaAPIView: tienda_id={tienda_id}, codigo={codigo}")

        # Intentar obtener la tienda
        try:
            tienda_enc = Tienda.objects.get(id_efsystem=tienda_id, activa=True)
        except Tienda.DoesNotExist:
            # Si la tienda no existe, devuelve un status 404 y URL vacía
#            Logger.add_to_log("error", f"Tienda no encontrada para id_efsystem={tienda_id}")
            return JsonResponse(
                {
                    "Resp": "",
                    "status": 0,
                    "encabezado": "",
                    "texto": "No existe tienda",
                    "codigo": ""
                },
                status=status.HTTP_200_OK
            )

        # Validar que la tienda esté asignada a la encuesta
        e_asignada = tienda_enc.encuestasFijas_asignadas_id()
        if e_asignada == "":
            # Si no tiene encuesta, devuelve un status 404 y URL vacía
#            Logger.add_to_log("warn", f"Tienda {tienda_id} no tiene encuesta asignada.")
            return JsonResponse(
                {
                    "Resp": "",
                    "status": 1,
                    "encabezado": "",
                    "texto": "No tiene encuesta asignada",
                    "codigo": ""
                },
                status=status.HTTP_200_OK
            )


        encuesta_asignada = EncuestaFija.objects.get(id=e_asignada)
        if encuesta_asignada:
            
            resp = tienda_enc.permite_premios_para(monto)
            if resp == 0:
                # Si no permite premios, devuelve un status 404 y URL vacía
                return JsonResponse(
                    {
                        "Resp": "",
                        "status": 2,
                        "encabezado": "",
                        "texto": "No cumple con monto mínimo para premios",
                        "codigo": ""
                    },
                    status=status.HTTP_200_OK
                )
            else:
                url = "https://rueda.efperfumes.com" + reverse('fijaConTicket', args=[tienda_enc.id, e_asignada, codigo])
    #            Logger.add_to_log("info", f"Encuesta asignada encontrada. Generando URL: {url}")
                TicketConsulta.objects.create(
                    tienda_id=tienda_enc.id,
                    codigo=codigo,
                    monto=monto,
                )
                return JsonResponse(
                    {
                        "Resp": url,
                        "status": 200,
                        "encabezado": encuesta_asignada.encabezado,
                        "texto": encuesta_asignada.texto,
                        "codigo": codigo
                    },
                    status=status.HTTP_200_OK
                )

