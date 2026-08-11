import pandas as pd
from sklearn.cluster import KMeans
import plotly.express as px
from tienda.models import Interaccion, Producto

def entrenar_clusters():
    # NUEVO: Traemos también el 'nombre' para que se vea al pasar el mouse
    productos = Producto.objects.all().values('id', 'nombre', 'precio', 'categoria_id')
    df = pd.DataFrame(list(productos))

    if df.empty:
        return None

    X = df[['precio', 'categoria_id']].fillna(0)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    
    # Lo convertimos a string (texto) para que Plotly use colores distintos por grupo
    df['cluster'] = kmeans.fit_predict(X).astype(str) 

    return df

def generar_grafico_clusters():
    df = entrenar_clusters()
    if df is None:
        return None

    # Magia de Plotly: Gráfica interactiva en 1 línea
    fig = px.scatter(df, x='categoria_id', y='precio', color='cluster', 
                     hover_data=['nombre'], # El nombre aparece al pasar el cursor
                     title='Clusters de Productos (IA)',
                     labels={'categoria_id': 'ID Categoría', 'precio': 'Precio ($)', 'cluster': 'Grupo'})
    
    # Esto quita el fondo blanco para que se adapte al diseño de tu página
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=40, b=20))
    
    # Generamos el código HTML interactivo
    return fig.to_html(full_html=False, include_plotlyjs='cdn')

def generar_grafico_usuario(usuario_id):
    interacciones = Interaccion.objects.filter(usuario_id=usuario_id).values('producto__categoria__nombre')
    df = pd.DataFrame(list(interacciones))

    if df.empty:
        return None

    # Preparamos los datos para Plotly
    resumen = df['producto__categoria__nombre'].value_counts().reset_index()
    resumen.columns = ['Categoría', 'Interacciones']

    # Creamos gráfica de barras interactiva
    fig = px.bar(resumen, x='Categoría', y='Interacciones', 
                 title='Tus Categorías Más Interesantes',
                 color='Categoría')
    
    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=40, b=20))
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')