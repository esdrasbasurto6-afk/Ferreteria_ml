from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from .models import Producto, Carrito, ItemCarrito, Orden, DetalleOrden, Interaccion
from .forms import RegistroForm

# --- IMPORTACIONES DESDE MOTOR_IA ---
from .motor_ia.recomendaciones import recomendaciones_hibridas
from .motor_ia.clustering import generar_grafico_clusters, generar_grafico_usuario
from .motor_ia.codo import generar_grafico_codo
from .motor_ia.segmentacion import segmentar_clientes_kmeans, generar_grafica_segmentacion
from .motor_ia.predicciones import ejecutar_modelo_prediccion
from .motor_ia.almacen_ia import analizar_almacen_ia
from .motor_ia.ejecutivo_ia import obtener_datos_ejecutivos

def landing(request):
    return render(request, 'landing.html')

def dashboard(request):
    # Traemos productos normales para la tienda
    productos = Producto.objects.all()[:20]

    recomendaciones = []
    if request.user.is_authenticated:
        # Llamamos a la función mejorada (ahora devuelve Producto + Motivo)
        recomendaciones = recomendaciones_hibridas(request.user.id)

    return render(request, 'dashboard.html', {
        'productos': productos,
        'recomendaciones': recomendaciones
    })

# --- VISTA PARA VER EL PRODUCTO Y REGISTRAR LA "VISTA" ---
def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.user.is_authenticated:
        Interaccion.objects.create(
            usuario=request.user,
            producto=producto,
            tipo='VISTA'
        )
        
    return render(request, 'detalle.html', {'producto': producto})

def agregar_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    item, created = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto
    )

    if not created:
        item.cantidad += 1
        item.save()

    if request.user.is_authenticated:
        Interaccion.objects.create(
            usuario=request.user,
            producto=producto,
            tipo='CARRITO'
        )

    return redirect('carrito')

def carrito(request):
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    items = ItemCarrito.objects.filter(carrito=carrito)
    total = sum(i.producto.precio * i.cantidad for i in items)

    return render(request, 'carrito.html', {
        'items': items,
        'total': total
    })

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RegistroForm()
    return render(request, 'registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('dashboard')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('landing')

def buscar(request):
    query = request.GET.get('q')
    resultados = Producto.objects.filter(nombre__icontains=query)[:20]
    return render(request, 'busqueda.html', {'resultados': resultados, 'query': query})

def checkout(request):
    carrito = Carrito.objects.get(usuario=request.user)
    items = ItemCarrito.objects.filter(carrito=carrito)
    total = sum(i.producto.precio * i.cantidad for i in items)

    orden = Orden.objects.create(usuario=request.user, total=total)

    for item in items:
        DetalleOrden.objects.create(
            orden=orden,
            producto=item.producto,
            cantidad=item.cantidad
        )
        Interaccion.objects.create(
            usuario=request.user,
            producto=item.producto,
            tipo='COMPRA'
        )

    detalles_comprados = DetalleOrden.objects.filter(orden=orden)
    items.delete() 

    return render(request, 'recibo.html', {
        'orden': orden,
        'detalles': detalles_comprados
    })

def reportes_analitica(request):
    grafico_clusters = generar_grafico_clusters()
    grafico_codo = generar_grafico_codo()
    
    grafico_usuario = None
    if request.user.is_authenticated:
        # Nota: Asumo que generar_grafico_usuario está en clustering.py
        grafico_usuario = generar_grafico_usuario(request.user.id)

    return render(request, 'analytics.html', {
        'grafico_clusters': grafico_clusters,
        'grafico_codo': grafico_codo,
        'grafico_usuario': grafico_usuario
    })

def dashboard_segmentacion(request):
    datos_clientes = segmentar_clientes_kmeans()
    grafica_html = generar_grafica_segmentacion(datos_clientes)
    
    # Calculamos los totales asegurando que siempre devuelvan un número (0 si no hay nadie)
    total_p = sum(1 for c in datos_clientes if c.get('tipo_cliente') == 'Premium')
    total_o = sum(1 for c in datos_clientes if c.get('tipo_cliente') == 'Ocasional')
    total_i = sum(1 for c in datos_clientes if c.get('tipo_cliente') == 'Inactivo')

    return render(request, 'segmentacion.html', {
        'datos_clientes': datos_clientes,
        'grafica': grafica_html,
        'total_premium': total_p,
        'total_ocasional': total_o,
        'total_inactivo': total_i
    })

# vista predicciones:
def dashboard_predicciones(request):
    tabla_datos, grafico_lineas, grafico_barras, grafico_pastel = ejecutar_modelo_prediccion()
    categorias = ['Herramientas', 'Electricidad', 'Pintura', 'Plomería', 'Tornillería']
    
    filas_historicas = [fila for fila in tabla_datos if 'Histórico' in fila['Tipo']]
    
    if filas_historicas:
        # Limpieza segura de datos para sumar los totales de las tarjetas
        totales = {}
        for cat in categorias:
            suma_cat = 0
            for fila in filas_historicas:
                valor = fila[cat]
                if isinstance(valor, str):
                    valor = valor.replace(' uds.', '')
                suma_cat += int(float(valor))
            totales[cat] = suma_cat
        
        categoria_top = max(totales, key=totales.get)
        producto_critico = min(totales, key=totales.get)
    else:
        categoria_top = "Herramientas"
        producto_critico = "Tornillería"

    crecimiento_ia = "+33.3%"

    return render(request, 'predicciones.html', {
        'tabla_datos': tabla_datos,
        'grafico_lineas': grafico_lineas,
        'grafico_barras': grafico_barras,
        'grafico_pastel': grafico_pastel,
        'categoria_top': categoria_top,
        'crecimiento_ia': crecimiento_ia,
        'producto_critico': producto_critico,
    })

# === Almacen  ===
def dashboard_almacen(request):
    # Ahora recibimos 6 variables en lugar de 5
    tabla_datos, grafica_html, kpi_criticos, kpi_saludable, kpi_sin_mov, texto_reporte = analizar_almacen_ia()

    context = {
        'tabla_datos': tabla_datos,
        'grafica_html': grafica_html,
        'kpi_criticos': kpi_criticos,
        'kpi_saludable': kpi_saludable,
        'kpi_sin_mov': kpi_sin_mov,
        'texto_reporte': texto_reporte  # <- Pasamos el texto redactado al HTML
    }
    
    return render(request, 'almacen.html', context)


def dashboard_ejecutivo(request):
    # 1. Ejecutamos el motor analítico para consolidar los datos de la BD
    datos_consolidados = obtener_datos_ejecutivos()

    # 2. Renderizamos la plantilla pasando el diccionario bajo la variable 'd'
    return render(request, 'ejecutivo.html', {'d': datos_consolidados})