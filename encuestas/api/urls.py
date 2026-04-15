from django.urls import path
from .views import EncuestaTiendaAPIView


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('enc_t/', EncuestaTiendaAPIView.as_view(), name='encuesta-tienda'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]