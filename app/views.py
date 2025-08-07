import io
import os
import uuid

import barcode
import camelot
import qrcode
from barcode.writer import ImageWriter
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, Sum
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from openpyxl.reader.excel import load_workbook

# Create your views here.
from rest_framework import viewsets, permissions, status, filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import permission_classes, api_view, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from DjangoProject import settings
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual, PDFUpload, ExcelUpload, Envio, EnvioDetalle, \
    Bodega, Familia, Notificacion, Pendiente
from .serializer import CargoSerializer, ProductoSerializer, IngresoSerializer, RetiroSerializer, UsuarioSerializer, \
    StockActualSerializer, ProductoStockSerializer, PDFUploadSerializer, ExcelUploadSerializer, UserSerializer, \
    EnvioSerializer, EnvioDetalleSerializer, BodegaSerializer, EnvioSerializerAnidado, FamiliaSerializer, \
    NotificacionSerializer, PendienteSerializer


# permissions.py

class SoloBodeguerosVenEnviosALaBodega(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.groups.filter(name="Bodeguero").exists():
            return obj.bodega_destino in user.bodegas.all()
        return True

class SoloBodeguerosVenStockDeSuBodega(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name="Bodeguero").exists()


class BodegueroNOT(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.is_active and not request.user.groups.filter(name='Bodeguero').exists():
            return True
        return False

class BodegueroYES(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated and  request.user.is_active:
            return True

class CurrentUserGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        groups = list(request.user.groups.values_list('name', flat=True))
        print(groups)
        return Response({"groups": groups})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [BodegueroNOT]
    

class FamiliaViewSet(viewsets.ModelViewSet):
    queryset = Familia.objects.all()
    serializer_class = FamiliaSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['padre']
    search_fields = ['nombre']

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    ordering = ['id']
    ordering_fields = ['nombre', 'codigo_barras']
    filterset_fields = ['codigo_barras', 'nombre', 'id', 'familia']
    search_fields = ['nombre', 'codigo_barras', 'descripcion']

class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['leido']

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True  # Permite actualizar solo algunos campos
        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

class ProductosEnMiBodegaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductoSerializer
    permission_classes = [IsAuthenticated, SoloBodeguerosVenStockDeSuBodega]

    def get_queryset(self):
        user = self.request.user
        bodegas = getattr(user, "bodegas", None)
        if bodegas is not None:
            # Filtra productos que tienen al menos un stock en bodegas del usuario
            return Producto.objects.filter(
                Exists(
                    StockActual.objects.filter(
                        producto=OuterRef('pk'),
                        bodega__in=bodegas.all()
                    )
                )
            ).distinct()
        return Producto.objects.none()


class ProductoStockViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('stock').all()
    serializer_class = ProductoStockSerializer
class IngresoViewSet(viewsets.ModelViewSet):
    queryset = Ingreso.objects.all()
    serializer_class = IngresoSerializer
    permission_classes = [BodegueroYES]

class RetiroViewSet(viewsets.ModelViewSet):
    queryset = Retiro.objects.all()
    serializer_class = RetiroSerializer
    permission_classes = [BodegueroYES]

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

class StockViewSet(viewsets.ModelViewSet):
    queryset = StockActual.objects.all()
    serializer_class = StockActualSerializer
    permission_classes = [IsAuthenticated]

class StockBajoStockViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockActualSerializer
    def get_queryset(self):
        return StockActual.objects.filter(cantidad__lt=5)

class StockDeMiBodegaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockActualSerializer
    permission_classes = [IsAuthenticated, SoloBodeguerosVenStockDeSuBodega]

    def get_queryset(self):
        user = self.request.user
        bodegas = getattr(user, "bodegas", None)
        if bodegas is not None:
            return StockActual.objects.filter(bodega__in=bodegas.all())
        return StockActual.objects.none()

class StockDeMiBodegaBajoStockViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockActualSerializer
    permission_classes = [IsAuthenticated, SoloBodeguerosVenStockDeSuBodega]

    def get_queryset(self):
        user = self.request.user
        bodegas = getattr(user, "bodegas", None)
        if bodegas is not None:
            return StockActual.objects.filter(bodega__in=bodegas.all()).filter(cantidad__lt=5)
        return StockActual.objects.none()
class EnvioViewSet(viewsets.ModelViewSet):
    queryset = Envio.objects.all()
    serializer_class = EnvioSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['confirmado', 'bodega_origen', 'bodega_destino']

class EnvioAnidadoViewSet(viewsets.ModelViewSet):
    queryset = Envio.objects.all().prefetch_related('detalles')
    serializer_class = EnvioSerializerAnidado
    permission_classes = [SoloBodeguerosVenEnviosALaBodega]
    name = 'EnvioAnidado'

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Bodeguero").exists():
            return Envio.objects.filter(bodega_destino__in=user.bodegas.all())
        return Envio.objects.all()


class EnvioDetalleViewSet(viewsets.ModelViewSet):
    queryset = EnvioDetalle.objects.all()
    serializer_class = EnvioDetalleSerializer

class BodegaViewSet(viewsets.ModelViewSet):
    queryset = Bodega.objects.all()
    serializer_class = BodegaSerializer

class PendienteViewSet(viewsets.ModelViewSet):
    queryset = Pendiente.objects.all().select_related('producto')
    serializer_class = PendienteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['producto', 'completado']
    search_fields = ['descripcion']

class PDFUploadView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, BodegueroNOT]

    def post(self, request):
        serializer = PDFUploadSerializer(data=request.data)
        if serializer.is_valid():
            pdf_obj = serializer.save()
            pdf_path = pdf_obj.archivo.path

            try:
                tables = camelot.read_pdf(pdf_path, pages='all')

                for table in tables:
                    df = table.df  # pandas DataFrame

                    # Ejemplo: asumir primera fila es encabezado
                    headers = df.iloc[0]
                    data_rows = df.iloc[1:]

                    for row in data_rows.itertuples(index=False):
                        row_dict = dict(zip(headers, row))

                        if row_dict.get("DETALLE") == "":
                            continue  # Salta esta fila
                        producto = Producto.objects.create(
                            nombre=row_dict.get("DETALLE"),
                            descripcion=row_dict.get("Descripción"),
                            codigo_barras=row_dict.get("Código de barras") or str(uuid.uuid4())[:20]
                        )
                        stock = StockActual.objects.get(producto_id=producto)
                        stock.cantidad = int(row_dict.get("CANTIDAD", 0))
                        stock.save()


                response = PDFUploadSerializer(pdf_obj)
                pdf_obj.delete()
                return Response(response.data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExcelUploadView(APIView):

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, BodegueroNOT]

    def post(self, request):
        serializer = ExcelUploadSerializer(data=request.data)
        if serializer.is_valid():
            excel_obj = serializer.save()
            archivo = serializer.validated_data['archivo']
            wb = load_workbook(filename=archivo, data_only=True)
            ws = wb.active

            headers = [cell.value for cell in ws[1]]
            for row in ws.iter_rows(min_row=2, values_only=True):
                row_data = dict(zip(headers, row))
                if not row_data.get("Nombre"):
                    continue

                producto = Producto.objects.create(
                    nombre=row_data.get("Nombre"),
                    descripcion=row_data.get("Descripción", ""),
                    codigo_barras=row_data.get("Código de barras") or str(uuid.uuid4())[:20],
                    centro_costo=row_data.get("Centro Costo")
                )



            response = ExcelUploadSerializer(excel_obj)
            excel_obj.delete()
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def barcode_image_on_demand(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return HttpResponse("Producto no encontrado", status=404)

    barcode_class = barcode.get_barcode_class('code128')
    buffer = io.BytesIO()
    barcode_class(producto.codigo_barras, writer=ImageWriter()).write(buffer)

    return HttpResponse(
        buffer.getvalue(),
        content_type="image/png",
        headers={
            'Content-Disposition': f'attachment; filename="{producto.codigo_barras}.png"'
        }
    )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def sqr_image_on_demand(request, pk):
    try:
        producto = Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return HttpResponse("Producto no encontrado", status=404)

    qr = qrcode.make(producto.codigo_barras)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')

    return HttpResponse(
        buffer.getvalue(),
        content_type="image/png",
        headers={
            'Content-Disposition': f'attachment; filename="{producto.codigo_barras}.png"'
        }
    )
