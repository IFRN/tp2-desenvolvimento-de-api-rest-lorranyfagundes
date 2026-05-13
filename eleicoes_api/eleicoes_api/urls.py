from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from urna.views import (
    EleitorViewSet, EleicaoViewSet, CandidatoViewSet, 
    AptidaoEleitorViewSet, RegistroVotacaoViewSet, VotoViewSet
)
# Swagger imports
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions



#Swagger
schema_view = get_schema_view(
   openapi.Info(
      title="API Urna Eletrônica",
      default_version='1',
      description="Sistema de Eleição",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

#Rotas
router = DefaultRouter()
router.register(r'eleitores', EleitorViewSet)
router.register(r'eleicoes', EleicaoViewSet)
router.register(r'candidatos', CandidatoViewSet)
router.register(r'aptidoes', AptidaoEleitorViewSet)
router.register(r'registros-votacao', RegistroVotacaoViewSet)
router.register(r'votos', VotoViewSet)

urlpatterns = [
    path('admin/', admin.site.core_admin_site if hasattr(admin.site, 'core_admin_site') else admin.site.urls),
    path('api/', include(router.urls)),
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc-ui'),
]