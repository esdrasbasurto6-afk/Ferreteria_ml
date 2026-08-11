import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from django.db.models import Sum

# Importamos tu modelo Producto
from ..models import Producto


def analizar_almacen_ia():

    # ==========================================
    # 1. EXTRACCIÓN DE DATOS REALES DE TU BD
    # ==========================================

    movimientos_db = Producto.objects.annotate(
        total_salidas=Sum('detalleorden__cantidad')
    ).values(
        'nombre',
        'stock',
        'total_salidas'
    )

    # Convertimos la consulta a DataFrame
    df = pd.DataFrame(list(movimientos_db))

    # ==========================================
    # 2. VALIDACIÓN
    # ==========================================

    if df.empty:

        return (
            [],
            """
            <div class='alert alert-warning rounded-4 shadow-sm'>
                No hay productos registrados.
            </div>
            """,
            0,
            0,
            0
        )

    # ==========================================
    # 3. LIMPIEZA DE DATOS
    # ==========================================

    df = df.rename(columns={
        'nombre': 'Producto',
        'stock': 'Stock',
        'total_salidas': 'Salidas'
    })

    # Rellenar nulos
    df['Salidas'] = df['Salidas'].fillna(0)

    # Convertir a enteros
    df['Salidas'] = df['Salidas'].astype(int)
    df['Stock'] = df['Stock'].astype(int)

    # Entradas simuladas
    df['Entradas'] = (
        df['Stock'] +
        df['Salidas']
    )

    # ==========================================
    # 4. IA HEURÍSTICA
    # ==========================================

    # Porcentaje de rotación
    df['Rotacion_Porcentaje'] = (

        df['Salidas'] /
        df['Entradas'].replace(0, 1)

    ) * 100

    df['Rotacion_Porcentaje'] = (
        df['Rotacion_Porcentaje']
        .round(1)
    )

    # ==========================================
    # 5. ESTADO INVENTARIO
    # ==========================================

    def evaluar_estado(stock):

        if stock <= 15:
            return '🔴 Crítico'

        elif stock <= 30:
            return '🟡 Alerta'

        return '🟢 Saludable'

    # ==========================================
    # 6. RECOMENDACIÓN IA
    # ==========================================

    def generar_recomendacion(row):

        # Crítico
        if row['Stock'] <= 15:

            return "⚠️ COMPRA URGENTE"

        # Baja rotación
        elif row['Rotacion_Porcentaje'] < 30:

            return "📉 GENERAR PROMOCIÓN"

        # Normal
        return "✅ MONITOREO NORMAL"

    df['Estado'] = df['Stock'].apply(
        evaluar_estado
    )

    df['Recomendacion'] = df.apply(
        generar_recomendacion,
        axis=1
    )

    # ==========================================
    # 7. ORDEN VISUAL
    # ==========================================

    prioridad_estado = {
        '🔴 Crítico': 0,
        '🟡 Alerta': 1,
        '🟢 Saludable': 2
    }

    df['Prioridad'] = (
        df['Estado']
        .map(prioridad_estado)
    )

    # Mostrar críticos arriba
    df = df.sort_values(
        by=['Prioridad', 'Stock']
    )

    # ==========================================
    # 8. COLORES DINÁMICOS
    # ==========================================

    colores_stock = []

    for estado in df['Estado']:

        if 'Crítico' in estado:

            colores_stock.append('#ef4444')

        elif 'Alerta' in estado:

            colores_stock.append('#f59e0b')

        else:

            colores_stock.append('#22c55e')

    # ==========================================
    # 9. DASHBOARD VISUAL MODERNO
    # ==========================================

    fig = go.Figure()

    # ------------------------------------------
    # ENTRADAS
    # ------------------------------------------

    fig.add_trace(go.Bar(

        name='Entradas',

        x=df['Producto'],

        y=df['Entradas'],

        marker=dict(
            color='#3b82f6',
            line=dict(
                color='#60a5fa',
                width=1
            )
        ),

        hovertemplate=
        '<b>%{x}</b><br>' +
        'Entradas: %{y}<extra></extra>'
    ))

    # ------------------------------------------
    # SALIDAS
    # ------------------------------------------

    fig.add_trace(go.Bar(

        name='Salidas',

        x=df['Producto'],

        y=df['Salidas'],

        marker=dict(
            color='#f59e0b',
            line=dict(
                color='#fbbf24',
                width=1
            )
        ),

        hovertemplate=
        '<b>%{x}</b><br>' +
        'Salidas: %{y}<extra></extra>'
    ))

    # ------------------------------------------
    # STOCK ACTUAL
    # ------------------------------------------

    fig.add_trace(go.Bar(

        name='Stock Actual',

        x=df['Producto'],

        y=df['Stock'],

        marker=dict(
            color=colores_stock,
            line=dict(
                color='rgba(255,255,255,.15)',
                width=1
            )
        ),

        hovertemplate=
        '<b>%{x}</b><br>' +
        'Stock: %{y}<extra></extra>'
    ))

    # ==========================================
    # 10. CONFIGURACIÓN VISUAL
    # ==========================================

    fig.update_layout(

        # Título
        title={
            'text': '📊 Análisis Inteligente de Inventario',
            'x': 0.5,
            'font': {
                'size': 24,
                'color': '#ffffff'
            }
        },

        # Tema oscuro moderno
        template='plotly_dark',

        # Fondos
        plot_bgcolor='#0f172a',
        paper_bgcolor='#0f172a',

        # Barras
        barmode='group',
        bargap=0.28,
        bargroupgap=0.12,

        # Altura
        height=850,

        # Hover elegante
        hovermode='x unified',

        # Márgenes
       margin=dict(
            l=20,
            r=20,
            t=80,
            b=180
        ),

        # Fuente global
        font=dict(
            family='Segoe UI',
            color='white'
        ),

        # Leyenda
        legend=dict(

            orientation='h',

            yanchor='bottom',

            y=-0.25,

            xanchor='center',

            x=0.5,

            bgcolor='rgba(0,0,0,0)',

            font=dict(
                size=12
            )
        ),

        # Eje X
        xaxis=dict(

            title='Productos',

            tickangle=-50,

            automargin=True,

            tickfont=dict(
                size=11
            ),

            gridcolor='rgba(255,255,255,.05)'
        ),

        # Eje Y
        yaxis=dict(

            title='Cantidad',

            gridcolor='rgba(255,255,255,.08)',

            zerolinecolor='rgba(255,255,255,.1)'
        )
    )

    # ==========================================
    # 11. EXPORTAR HTML
    # ==========================================

    grafica_html = pio.to_html(

        fig,

        full_html=False,

        config={

            # Responsive
            'responsive': True,

            # Mostrar barra
            'displayModeBar': True,

            # Zoom
            'scrollZoom': True,

            # Quitar logo
            'displaylogo': False,

            # Quitar botones innecesarios
            'modeBarButtonsToRemove': [
                'lasso2d',
                'select2d'
            ]
        }
    )

    # ... (Todo tu código anterior se queda igual hasta el cálculo de KPIs) ...

    # ==========================================
    # 6. CÁLCULO DE KPIs
    # ==========================================
    total_productos = len(df)
    kpi_criticos = int((df['Stock'] <= 15).sum())
    kpi_saludable = round((int((df['Stock'] > 15).sum()) / total_productos) * 100, 1)
    kpi_sin_mov = int((df['Rotacion_Porcentaje'] < 10).sum())

    # ==========================================
    # 7. IA DE REDACCIÓN (Generación de Lenguaje)
    # ==========================================
    import datetime
    fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y")
    
    # Extraemos nombres de productos críticos para mencionarlos
    prod_criticos_lista = df[df['Stock'] <= 15]['Producto'].tolist()
    nombres_criticos = ", ".join(prod_criticos_lista[:3]) # Tomamos los 3 primeros
    if len(prod_criticos_lista) > 3: nombres_criticos += " y otros"

    # Redacción automática del reporte
    texto_reporte = (
        f"Con base en el análisis de datos procesado el <b>{fecha_actual}</b>, "
        f"el sistema heurístico reporta que el <b>{kpi_saludable}%</b> del inventario se encuentra "
        f"en un estado óptimo de flujo y rotación comercial.<br><br>"
    )

    if kpi_criticos > 0:
        texto_reporte += (
            f"<b>ALERTA DE DESABASTO:</b> Se ha detectado una anomalía crítica. <b>{kpi_criticos} producto(s)</b> "
            f"han alcanzado niveles de inventario inferiores al mínimo permitido (destacando: <i>{nombres_criticos}</i>). "
            f"La Inteligencia Artificial recomienda emitir órdenes de compra urgentes bajo el esquema Just-In-Time para evitar "
            f"la interrupción de las ventas y pérdida de ganancias.<br><br>"
        )
    else:
        texto_reporte += "Actualmente no se detectan artículos con riesgo de desabasto inmediato.<br><br>"

    if kpi_sin_mov > 0:
        texto_reporte += (
            f"<b>ALERTA DE ESTANCAMIENTO:</b> El algoritmo identificó <b>{kpi_sin_mov} artículo(s)</b> con un índice de "
            f"rotación excepcionalmente bajo. Se sugiere a gerencia implementar estrategias de marketing o "
            f"promociones para liberar el capital congelado en los anaqueles."
        )
    else:
        texto_reporte += "El flujo de salidas mantiene un ritmo constante, sin mercancía estancada detectada."


    # ==========================================
    # 8. RETORNO FINAL (¡Agregamos el texto al final!)
    # ==========================================
    return df.to_dict('records'), grafica_html, kpi_criticos, kpi_saludable, kpi_sin_mov, texto_reporte