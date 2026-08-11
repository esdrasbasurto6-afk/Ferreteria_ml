import pandas as pd
from sklearn.cluster import KMeans
from django.db.models import Sum, Count
from tienda.models import Orden
import plotly.express as px
import plotly.io as pio

def segmentar_clientes_kmeans():
    # --- PASO 1: OBTENCIÓN DE DATOS ---
    # Extraemos el total gastado y la frecuencia de compra desde MySQL vía Django ORM
    datos_compras = Orden.objects.values(
        'usuario__id', 
        'usuario__username'
    ).annotate(
        total_gastado=Sum('total'),
        frecuencia=Count('id')
    )

    df = pd.DataFrame(list(datos_compras))

    if df.empty:
        return []
    
    # --- PASO 2: LIMPIEZA DE DATOS ---
    # 1. Eliminar registros vacíos
    df = df.dropna()
    # 2. Eliminar datos repetidos (usuarios duplicados)
    df = df.drop_duplicates(subset=['usuario__id'])
    # 3. Eliminar valores incorrectos (compras en $0 o negativas)
    df = df[df['total_gastado'] > 0]

    # Verificamos que no se haya quedado vacío tras la limpieza
    if df.empty:
        return []

    # --- PASO 3: APLICAR ALGORITMO K-MEANS ---
    # Ajustamos el número de clusters al número de datos disponibles (máximo 3 grupos)
    n_clusters = min(len(df), 3)
    
    if n_clusters > 0:
        # Configuración del modelo K-Means
        modelo = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['cluster'] = modelo.fit_predict(df[['total_gastado', 'frecuencia']])
        
        # Ordenamos los centros matemáticos para identificar automáticamente el nivel adquisitivo
        centros = df.groupby('cluster')['total_gastado'].mean().sort_values(ascending=False)
        
        # Asignación segura de nombres a los Clusters
        mapeo_nombres = {}
        if len(centros) >= 1: mapeo_nombres[centros.index[0]] = 'Premium'   # Cluster con más gasto
        if len(centros) >= 2: mapeo_nombres[centros.index[1]] = 'Ocasional' # Cluster con gasto medio
        if len(centros) >= 3: mapeo_nombres[centros.index[2]] = 'Inactivo'  # Cluster con menor gasto
        
        df['tipo_cliente'] = df['cluster'].map(mapeo_nombres)
    else:
        df['tipo_cliente'] = 'Sin Clasificar'

    return df.to_dict('records')

def generar_grafica_segmentacion(datos_segmentados):
    if not datos_segmentados:
        return None

    df = pd.DataFrame(datos_segmentados)
    conteo = df['tipo_cliente'].value_counts().reset_index()
    conteo.columns = ['Tipo de Cliente', 'Cantidad']

    colores = {'Premium': '#FFD700', 'Ocasional': '#1E90FF', 'Inactivo': '#FF6347'}

    fig = px.bar(
        conteo, x='Tipo de Cliente', y='Cantidad',
        color='Tipo de Cliente', color_discrete_map=colores,
        text='Cantidad', title="Distribución de Clientes"
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        margin=dict(l=20, r=20, t=40, b=20), 
        showlegend=False
    )
    return pio.to_html(fig, full_html=False)