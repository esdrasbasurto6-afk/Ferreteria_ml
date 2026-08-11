from django.contrib import admin
from .models import Categoria, Producto, Orden, Interaccion

# Aquí le decimos a Django que queremos administrar estas tablas en el CRUD
admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Orden)
admin.site.register(Interaccion)