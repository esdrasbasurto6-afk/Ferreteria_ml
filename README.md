```md
# Ferretería ML

Aplicación web de comercio electrónico para una ferretería, desarrollada con Django e integrada con herramientas de análisis de datos y Machine Learning para recomendar productos, segmentar clientes, predecir ventas y monitorear el inventario.

## Características

- Catálogo de productos con categorías, precios, stock y búsqueda.
- Registro, inicio de sesión y gestión de usuarios.
- Carrito de compras, checkout y generación de órdenes.
- Registro de interacciones de usuarios y compras.
- Recomendaciones personalizadas de productos.
- Segmentación de clientes mediante K-Means.
- Predicción de ventas mediante regresión lineal.
- Dashboard de inventario con alertas de productos críticos.
- Panel ejecutivo con indicadores de ventas, inventario y desempeño.
- API REST para consultar productos.

## Tecnologías

- Python
- Django
- MySQL
- Django REST Framework
- Pandas y NumPy
- Scikit-learn
- Matplotlib y Plotly
- HTML, CSS y JavaScript

## Modelos de Machine Learning

- **Sistema de recomendaciones híbrido:** sugiere productos según las interacciones, compras y categorías de interés del usuario.
- **K-Means:** agrupa productos y segmenta clientes según su comportamiento de compra.
- **Regresión lineal:** genera predicciones de ventas por categoría.
- **Análisis de inventario:** identifica niveles críticos de stock y productos sin movimiento.

## Instalación

1. Clona el repositorio:

   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd Ferreteria_ml-main
   ```

2. Crea y activa un entorno virtual:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Crea una base de datos MySQL llamada `ferreteria` e importa el archivo `BaseDatos.sql`.

5. Configura las credenciales de MySQL en `ferreteria_ml/settings.py`.

6. Ejecuta las migraciones:

   ```bash
   python manage.py migrate
   ```

7. Inicia el servidor:

   ```bash
   python manage.py runserver
   ```

8. Abre el proyecto en:

   ```text
   http://127.0.0.1:8000/
   ```

## Autor

**Esdras Josué Basurto Sandoval**  
[GitHub](https://github.com/esdrasbasurto6-afk)
```
