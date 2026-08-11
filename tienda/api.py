from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Producto


@api_view(['GET'])
def productos_api(request):
    productos = Producto.objects.all()[:50]

    data = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "precio": p.precio
        }
        for p in productos
    ]

    return Response(data)