import pandas as pd
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

# Importa tus modelos (Asegúrate de que los nombres coincidan con los de tu models.py)
from ..models import Producto, Orden, DetalleOrden 
# Importamos el motor que ya creamos para no repetir código
from .almacen_ia import analizar_almacen_ia

def obtener_datos_ejecutivos():
    # ==========================================
    # 1. TRAER INTELIGENCIA DEL ALMACÉN
    # ==========================================
    try:
        tabla_inventario, _, kpi_criticos, kpi_saludable, kpi_sin_mov, _ = analizar_almacen_ia()
        df_inv = pd.DataFrame(tabla_inventario)
    except Exception as e:
        # Prevención de caída del dashboard si el almacén falla
        df_inv = pd.DataFrame()
        kpi_criticos = kpi_saludable = kpi_sin_mov = 0

    # ==========================================
    # 2. STATUS GLOBAL Y TICKET PROMEDIO
    # ==========================================
    total_ventas_historico = Orden.objects.aggregate(total=Sum('total'))['total'] or 0
    pedidos_totales = Orden.objects.count()
    
    # KPI Gerencial: Ticket Promedio de Compra
    ticket_promedio = (total_ventas_historico / pedidos_totales) if pedidos_totales > 0 else 0

    # ==========================================
    # 3. BALANCE FINANCIERO (Hoy, Semana, Mes)
    # ==========================================
    hoy = timezone.now().date()
    
    ventas_hoy = Orden.objects.filter(
        fecha__date=hoy
    ).aggregate(total=Sum('total'))['total'] or 0
    
    ventas_semana = Orden.objects.filter(
        fecha__date__gte=hoy - timedelta(days=7)
    ).aggregate(total=Sum('total'))['total'] or 0
    
    ventas_mes = Orden.objects.filter(
        fecha__month=hoy.month, 
        fecha__year=hoy.year
    ).aggregate(total=Sum('total'))['total'] or 0

    # ==========================================
    # 4. INTELIGENCIA Y SEGMENTACIÓN DE CLIENTES
    # ==========================================
    # A) Los 4 clientes que más dinero han dejado
    top_clientes_db = Orden.objects.values('usuario__username').annotate(
        total_gastado=Sum('total')
    ).order_by('-total_gastado')[:4]

    # B) Segmentación para la gráfica de Dona (Frecuentes vs Ocasionales)
    # Contamos cuántas órdenes tiene cada usuario
    conteo_compras = Orden.objects.values('usuario').annotate(num_compras=Count('id'))
    
    clientes_ocasionales = conteo_compras.filter(num_compras=1).count()
    clientes_frecuentes = conteo_compras.filter(num_compras__gt=1).count()
    total_clientes_clasificados = clientes_ocasionales + clientes_frecuentes

    # Calculamos porcentajes seguros (evitando división entre 0)
    if total_clientes_clasificados > 0:
        pct_frecuentes = int((clientes_frecuentes / total_clientes_clasificados) * 100)
        pct_ocasionales = 100 - pct_frecuentes
    else:
        pct_frecuentes = 0
        pct_ocasionales = 0

    # ==========================================
    # 5. FILTROS DE IA PARA EL DASHBOARD
    # ==========================================
    if not df_inv.empty:
        # Aseguramos que las columnas existan antes de filtrar
        columnas = df_inv.columns.tolist()
        
        # Los 3 productos que MÁS se venden
        if 'Salidas' in columnas:
            top_volumen = df_inv.sort_values(by='Salidas', ascending=False).head(3).to_dict('records')
        else:
            top_volumen = []
            
        # Alertas críticas y sugerencias de compra
        if 'Estado' in columnas and 'Recomendacion' in columnas:
            alertas_top = df_inv[df_inv['Estado'].str.contains('Crítico', na=False)].head(3).to_dict('records')
            sugerencias = df_inv[df_inv['Recomendacion'].str.contains('COMPRA|URGENTE', na=False, regex=True)].head(4).to_dict('records')
        else:
            alertas_top = []
            sugerencias = []
    else:
        top_volumen = []
        alertas_top = []
        sugerencias = []

    # ==========================================
    # 6. RETORNO DE PAQUETE DE DATOS
    # ==========================================
    return {
        'ventas_total': total_ventas_historico,
        'pedidos_totales': pedidos_totales,
        'ticket_promedio': ticket_promedio,
        'ventas_hoy': ventas_hoy,
        'ventas_semana': ventas_semana,
        'ventas_mes': ventas_mes,
        'top_clientes': list(top_clientes_db),
        'pct_frecuentes': pct_frecuentes,
        'pct_ocasionales': pct_ocasionales,
        'top_volumen': top_volumen,
        'alertas_top': alertas_top,
        'sugerencias': sugerencias,
        'kpi_criticos': kpi_criticos,
        'kpi_saludable': kpi_saludable,
        'kpi_sin_mov': kpi_sin_mov
    }