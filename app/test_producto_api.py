import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from app.models import Producto, Gerencia
from app.serializer import ProductoSerializer

@pytest.fixture
def api_client():
    return APIClient()

@pytest.mark.django_db
def test_create_producto_without_codigo_barras():
    gerencia = Gerencia.objects.create(nombre="Test Gerencia")
    data = {
        "nombre": "Producto Test",
        "precio": 100,
        "gerencia": gerencia.id
    }
    serializer = ProductoSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    producto = serializer.save()
    
    assert producto.codigo_barras is not None
    assert len(producto.codigo_barras) > 0
    print(f"Generated barcode: {producto.codigo_barras}")

@pytest.mark.django_db
def test_create_producto_with_empty_codigo_barras():
    gerencia = Gerencia.objects.create(nombre="Test Gerencia 2")
    data = {
        "nombre": "Producto Test 2",
        "precio": 200,
        "gerencia": gerencia.id,
        "codigo_barras": ""
    }
    serializer = ProductoSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    producto = serializer.save()
    
    assert producto.codigo_barras is not None
    assert len(producto.codigo_barras) > 0
    print(f"Generated barcode for empty string: {producto.codigo_barras}")

@pytest.mark.django_db
def test_generar_codigo_action(api_client):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(username="testuser", password="password")
    api_client.force_authenticate(user=user)
    
    # La URL de un router DefaultRouter para un action detail=False es /api/productos/generar_codigo/
    url = "/api/productos/generar_codigo/"
    response = api_client.get(url)
    
    assert response.status_code == 200
    assert "codigo_barras" in response.data
    assert len(response.data["codigo_barras"]) > 0
    assert len(response.data["codigo_barras"]) <= 20
    
    # Verificar que el código generado no existe aún
    assert not Producto.objects.filter(codigo_barras=response.data["codigo_barras"]).exists()
