import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# --- IMPORTS PARA LA BASE DE DATOS DE DJANGO ---
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from tienda.models import DetalleOrden  # Cambia 'tienda' si tu app se llama distinto


def obtener_datos_reales():
    """Consulta directa a la Base de Datos incluyendo Mes y Año"""

    ventas_db = DetalleOrden.objects.annotate(
        anio=ExtractYear('orden__fecha'),
        mes_num=ExtractMonth('orden__fecha')
    ).values(
        'anio',
        'mes_num',
        'producto__categoria__nombre'
    ).annotate(
        total_unidades=Sum('cantidad')
    ).order_by('anio', 'mes_num')

    # Convertimos a DataFrame de Pandas
    df_raw = pd.DataFrame(list(ventas_db))

    # Pivotamos para tener categorías como columnas
    df_pivot = df_raw.pivot(
        index=['anio', 'mes_num'],
        columns='producto__categoria__nombre',
        values='total_unidades'
    ).fillna(0).reset_index()

    # Orden cronológico
    df_pivot = df_pivot.sort_values(
        by=['anio', 'mes_num']
    ).reset_index(drop=True)

    # Índice secuencial para IA
    df_pivot['Mes_Secuencial'] = df_pivot.index + 1

    # Traducción de meses
    nombres_meses = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre'
    }

    # Etiqueta Mes + Año
    df_pivot['Mes'] = df_pivot.apply(
        lambda r: f"{nombres_meses[int(r['mes_num'])]} {int(r['anio'])}",
        axis=1
    )

    # Categorías requeridas
    categorias_req = [
        'Herramientas',
        'Electricidad',
        'Pintura',
        'Plomería',
        'Tornillería'
    ]

    for cat in categorias_req:
        if cat not in df_pivot.columns:
            df_pivot[cat] = 0

    return df_pivot


def ejecutar_modelo_prediccion():

    df_hist = obtener_datos_reales()

    categorias = [
        'Herramientas',
        'Electricidad',
        'Pintura',
        'Plomería',
        'Tornillería'
    ]

    etiqueta_historico = 'Histórico (Base de Datos)'

    # =========================================================
    # ENTRENAMIENTO IA
    # =========================================================

    X_train = df_hist[['Mes_Secuencial']].values

    ultimo_anio = int(df_hist['anio'].max())

    ultimo_mes_num = int(
        df_hist[df_hist['anio'] == ultimo_anio]['mes_num'].max()
    )

    ultimo_secuencial = df_hist['Mes_Secuencial'].max()

    nombres_meses = {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Septiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre'
    }

    meses_futuros = []

    for i in range(1, 3):

        prox_mes = ultimo_mes_num + i
        prox_anio = ultimo_anio

        if prox_mes > 12:
            prox_mes -= 12
            prox_anio += 1

        nombre_label = f"{nombres_meses[prox_mes]} {prox_anio}"

        meses_futuros.append({
            'Mes': nombre_label,
            'Mes_Secuencial': ultimo_secuencial + i
        })

    df_futuro = pd.DataFrame(meses_futuros)

    X_future = df_futuro[['Mes_Secuencial']].values

    # =========================================================
    # REGRESIÓN LINEAL
    # =========================================================

    for cat in categorias:

        y_train = df_hist[cat].values

        modelo = LinearRegression()

        modelo.fit(X_train, y_train)

        predicciones = modelo.predict(X_future)

        df_futuro[cat] = np.clip(
            np.round(predicciones),
            0,
            None
        ).astype(int)

    df_hist['Tipo'] = etiqueta_historico
    df_futuro['Tipo'] = 'Predicción IA 🤖'

    df_completo = pd.concat(
        [df_hist, df_futuro],
        ignore_index=True
    )

    # =========================================================
    # COLORES
    # =========================================================

    colores = {
        'Herramientas': '#f59e0b',
        'Electricidad': '#3b82f6',
        'Pintura': '#10b981',
        'Plomería': '#ec4899',
        'Tornillería': '#6b7280'
    }

    # =========================================================
    # GRAFICA 1 - LINEAS
    # =========================================================

    fig_lineas = go.Figure()

    for cat in categorias:

        fig_lineas.add_trace(
            go.Scatter(
                x=df_completo['Mes'],
                y=df_completo[cat],
                mode='lines+markers',
                name=cat,
                line=dict(
                    color=colores[cat],
                    width=3
                )
            )
        )

   # MEJORA VISUAL Y CENTRADO DE LA GRÁFICA DE LÍNEAS
    fig_lineas.update_layout(
        template="plotly_white",
        height=450,  # Le damos la misma altura que a la de pastel para que se vean uniformes
        margin=dict(l=40, r=40, t=60, b=0), # Ajustamos márgenes
        
        # Centramos el título
        title=dict(
            text="Tendencias y Predicción de Demanda",
            x=0.5,
            xanchor='center'
        ),
        
        xaxis_title="Mes y Año",
        yaxis_title="Unidades Vendidas",
        
        # Movemos la leyenda a la parte inferior (igual que en el pastel)
        legend=dict(
            orientation='h',
            yanchor='top',
            y=-0.2,  # La empujamos un poco hacia abajo
            xanchor='center',
            x=0.5
        )
    )

    # =========================================================
    # GRAFICA 2 - BARRAS
    # =========================================================

    ventas_totales = df_completo[categorias].sum().reset_index()

    ventas_totales.columns = [
        'Categoría',
        'Unidades'
    ]

    fig_barras = px.bar(
        ventas_totales,
        x='Categoría',
        y='Unidades',
        color='Categoría',
        color_discrete_map=colores,
        text_auto=True,
        title="Volumen Total de Ventas Acumulado"
    )

    fig_barras.update_layout(
        template="plotly_white",
        showlegend=False
    )

    # =========================================================
    # GRAFICA 3 - PASTEL CENTRADO
    # =========================================================

    ventas_actuales = df_hist[categorias].sum().to_dict()

    df_pastel = pd.DataFrame(
        list(ventas_actuales.items()),
        columns=['Categoría', 'Ventas']
    )

    fig_pastel = px.pie(
        df_pastel,
        values='Ventas',
        names='Categoría',
        color='Categoría',
        color_discrete_map=colores,
        hole=0.45,
        title="Distribución de Mercado Actual"
    )

    # Estilo del pastel
    fig_pastel.update_traces(
        textposition='inside',
        textinfo='percent+label',
        pull=[0.02, 0.02, 0.02, 0.02, 0.02]
    )

    # CENTRADO
    fig_pastel.update_layout(

        template='plotly_white',

        height=450,

        margin=dict(
            l=0,
            r=0,
            t=60,
            b=0
        ),

        title=dict(
            x=0.5,
            xanchor='center'
        ),

        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.15,
            xanchor='center',
            x=0.5
        )
    )

    # =========================================================
    # RETORNO HTML
    # =========================================================

    return (

        df_completo.to_dict('records'),

        pio.to_html(
            fig_lineas,
            full_html=False,
            config={
                'displayModeBar': False,
                'responsive': True
            }
        ),

        pio.to_html(
            fig_barras,
            full_html=False,
            config={
                'displayModeBar': False,
                'responsive': True
            }
        ),

        pio.to_html(
            fig_pastel,
            full_html=False,
            config={
                'displayModeBar': False,
                'responsive': True
            }
        )

    )