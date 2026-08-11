from django.urls import path
from . import views
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Producto
from .views import *
from .api import productos_api

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # --- NUEVA RUTA PARA EL DETALLE DEL PRODUCTO ---
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('carrito/', views.carrito, name='carrito'),
    path('agregar/<int:producto_id>/', views.agregar_carrito, name='agregar_carrito'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro, name='registro'),
    path('buscar/', views.buscar, name='buscar'),
    path('api/productos/', productos_api, name='api_productos'),
    path('checkout/', views.checkout, name='checkout'),
    path('analytics/', views.reportes_analitica, name='analytics'),
    path('segmentacion/', views.dashboard_segmentacion, name='dashboard_segmentacion'),
    path('predicciones/', views.dashboard_predicciones, name='dashboard_predicciones'),
    path('almacen/', views.dashboard_almacen, name='dashboard_almacen'),
    path('ejecutivo/', views.dashboard_ejecutivo, name='dashboard_ejecutivo'),
    
]