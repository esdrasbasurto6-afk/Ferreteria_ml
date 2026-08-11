import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from tienda.models import Interaccion, Producto

def recomendaciones_hibridas(usuario_id, limite=10):
    interacciones = Interaccion.objects.all().values('usuario_id', 'producto_id', 'tipo')
    df = pd.DataFrame(list(interacciones))

    # Caso 1: No hay datos en la App
    if df.empty:
        productos = Producto.objects.order_by('?')[:limite]
        return [{'producto': p, 'motivo': 'Tendencia actual'} for p in productos]

    df['rating'] = df['tipo'].apply(lambda x: 3 if x == 'COMPRA' else (2 if x == 'CARRITO' else 1))

    matriz = df.pivot_table(
        index='usuario_id',
        columns='producto_id',
        values='rating',
        aggfunc='sum'
    ).fillna(0)

    # Caso 2: El usuario es nuevo o no tiene interacciones
    if usuario_id not in matriz.index:
        productos = Producto.objects.order_by('?')[:limite]
        return [{'producto': p, 'motivo': 'Popular en la tienda'} for p in productos]

    # --- Lógica de Recomendación ---
    productos_usuario = df[df['usuario_id'] == usuario_id]['producto_id'].tolist()
    recomendaciones_finales = []
    ids_vistos = set(productos_usuario)

    # 🔹 1. COLABORATIVO (Similitud de usuarios)
    similitud = cosine_similarity(matriz)
    df_sim = pd.DataFrame(similitud, index=matriz.index, columns=matriz.index)
    similares = df_sim.loc[usuario_id].sort_values(ascending=False)[1:6].index

    for u in similares:
        productos_vecino = df[df['usuario_id'] == u]['producto_id'].unique()
        for p_id in productos_vecino:
            if p_id not in ids_vistos:
                p = Producto.objects.get(id=p_id)
                recomendaciones_finales.append({
                    'producto': p, 
                    'motivo': 'Comprado por usuarios similares'
                })
                ids_vistos.add(p_id)
        if len(recomendaciones_finales) >= (limite // 2): break

    # 🔹 2. CONTENIDO (Misma categoría)
    categorias = Producto.objects.filter(id__in=productos_usuario).values_list('categoria', flat=True).distinct()
    productos_similares = Producto.objects.filter(categoria__in=categorias).exclude(id__in=ids_vistos).order_by('?')

    for p in productos_similares:
        recomendaciones_finales.append({
            'producto': p, 
            'motivo': f'Porque te interesa {p.categoria.nombre}'
        })
        ids_vistos.add(p.id)
        if len(recomendaciones_finales) >= limite: break

    return recomendaciones_finales[:limite]