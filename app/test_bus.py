import pytest
from app.models import Producto, Bodega, StockActual, Gerencia, Ingreso
from django.contrib.auth import get_user_model
from app.serializer import IngresoSerializer, RetiroSerializer

User = get_user_model()

@pytest.mark.django_db
def test_bus_centralizes_stock_management():
    # Setup
    gerencia = Gerencia.objects.create(nombre="Test Gerencia")
    producto = Producto.objects.create(nombre="P1", precio=10, gerencia=gerencia, codigo_barras="C1")
    bodega = Bodega.objects.create(nombre="B1")
    user = User.objects.create_user(username="u1", password="p1")

    # 1. Test Ingreso (Crea stock vía Bus)
    serializer = IngresoSerializer(data={
        "producto": producto.id,
        "usuario": user.id,
        "bodega": bodega.id,
        "cantidad": 10
    })
    assert serializer.is_valid()
    serializer.save()
    
    stock = StockActual.objects.get(producto=producto, bodega=bodega)
    assert stock.cantidad == 10

    # 2. Test Retiro (Reduce stock vía Bus)
    serializer = RetiroSerializer(data={
        "producto": producto.id,
        "usuario": user.id,
        "bodega": bodega.id,
        "cantidad": 4
    })
    assert serializer.is_valid()
    serializer.save()
    
    stock.refresh_from_db()
    assert stock.cantidad == 6

    # 3. Test Eliminación a Cero (Centralizado en el Handler)
    serializer = RetiroSerializer(data={
        "producto": producto.id,
        "usuario": user.id,
        "bodega": bodega.id,
        "cantidad": 6
    })
    assert serializer.is_valid()
    serializer.save()
    
    # El registro debería haber sido eliminado por el StockHandler
    assert not StockActual.objects.filter(producto=producto, bodega=bodega).exists()
