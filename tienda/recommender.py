import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib
import io
import urllib, base64
from .models import Interaccion, Producto, Categoria

# Configuramos matplotlib para que no intente abrir ventanas visuales en el servidor
matplotlib.use('Agg')

# ==========================================
# 1. SISTEMA DE RECOMENDACIONES (Ya lo tenías)
# ==========================================
def recomendaciones_hibridas(usuario_id, limite=10):
    interacciones = Interaccion.objects.all().values('usuario_id', 'producto_id', 'tipo')
    df = pd.DataFrame(list(interacciones))

    if df.empty:
        return Producto.objects.order_by('?')[:limite]

    df['rating'] = df['tipo'].apply(lambda x: 3 if x == 'COMPRA' else 1)

    matriz = df.pivot_table(
        index='usuario_id',
        columns='producto_id',
        values='rating',
        aggfunc='sum'
    ).fillna(0)

    if usuario_id not in matriz.index:
        return Producto.objects.order_by('?')[:limite]

    # 🔹 COLABORATIVO
    similitud = cosine_similarity(matriz)
    df_sim = pd.DataFrame(similitud, index=matriz.index, columns=matriz.index)

    similares = df_sim.loc[usuario_id].sort_values(ascending=False)[1:6].index

    productos_usuario = df[df['usuario_id'] == usuario_id]['producto_id'].tolist()

    recomendados = set()

    for u in similares:
        productos = df[df['usuario_id'] == u]['producto_id'].tolist()
        recomendados.update(productos)

    # 🔹 CONTENIDO (misma categoría)
    categorias = Producto.objects.filter(id__in=productos_usuario).values_list('categoria', flat=True)
    productos_similares = Producto.objects.filter(categoria__in=categorias)

    # 🔹 FUSIÓN
    final_ids = list(recomendados) + list(productos_similares.values_list('id', flat=True))

    return Producto.objects.filter(id__in=final_ids).exclude(id__in=productos_usuario)[:limite]


# ==========================================
# 2. SISTEMA DE APRENDIZAJE: CLUSTERS (NUEVO)
# ==========================================
def entrenar_clusters():
    # Extraemos los productos para agruparlos por su Precio y su Categoría
    productos = Producto.objects.all().values('id', 'precio', 'categoria_id')
    df = pd.DataFrame(list(productos))

    if df.empty:
        return None

    # Características a evaluar
    X = df[['precio', 'categoria_id']]

    # Algoritmo K-Means: Agrupamos en 4 clusters (perfiles de productos)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X)

    return df

def generar_grafico_clusters():
    df = entrenar_clusters()
    if df is None:
        return None

    plt.figure(figsize=(8, 6))
    # Creamos un gráfico de dispersión (Scatter plot)
    scatter = plt.scatter(df['categoria_id'], df['precio'], c=df['cluster'], cmap='viridis', s=50, alpha=0.7)
    plt.title('Clusters de Productos (IA)')
    plt.xlabel('ID de Categoría')
    plt.ylabel('Precio del Producto ($)')
    plt.colorbar(scatter, label='Grupo (Cluster)')

    # Convertimos la gráfica a una imagen base64 para mandarla al HTML
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    plt.close()
    return uri


# ==========================================
# 3. REPORTE DEL USUARIO (NUEVO)
# ==========================================
def generar_grafico_usuario(usuario_id):
    # Buscamos qué categorías de productos mira o compra más el usuario
    interacciones = Interaccion.objects.filter(usuario_id=usuario_id).values('producto__categoria__nombre')
    df = pd.DataFrame(list(interacciones))

    if df.empty:
        return None

    # Contamos las interacciones por categoría
    resumen = df['producto__categoria__nombre'].value_counts()

    plt.figure(figsize=(8, 6))
    resumen.plot(kind='bar', color='coral', edgecolor='black')
    plt.title('Tus Categorías Más Interesantes')
    plt.xlabel('Categoría')
    plt.ylabel('Cantidad de Interacciones (Vistas/Compras)')
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    plt.close()
    return uri