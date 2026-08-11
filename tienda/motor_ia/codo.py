import pandas as pd
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib
import io
import urllib, base64
from tienda.models import Producto

matplotlib.use('Agg')

def generar_grafico_codo():
    productos = Producto.objects.all().values('id', 'precio', 'categoria_id')
    df = pd.DataFrame(list(productos))
    
    if df.empty or len(df) < 3:
        return None
        
    X = df[['precio', 'categoria_id']].fillna(0)
    inercia = []
    rango_k = range(1, min(11, len(X) + 1)) 
    
    for k in rango_k:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X)
        inercia.append(kmeans.inertia_)
        
    plt.figure(figsize=(8, 5))
    plt.plot(rango_k, inercia, marker='o', linestyle='-', color='#007bff', linewidth=2, markersize=8)
    plt.title('Método del Codo para optimizar K-Means', fontsize=14, fontweight='bold')
    plt.xlabel('Número de Clusters (k)', fontsize=12)
    plt.ylabel('Inercia', fontsize=12)
    plt.xticks(rango_k)
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    string = base64.b64encode(buf.read())
    uri = urllib.parse.quote(string)
    plt.close()
    
    return uri