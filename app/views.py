import os
import uuid

import camelot
from django.http import FileResponse, Http404
from django.shortcuts import render
from openpyxl.reader.excel import load_workbook

# Create your views here.
from rest_framework import viewsets, permissions, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from DjangoProject import settings
from .models import Cargo, Producto, Ingreso, Retiro, Usuario, StockActual, PDFUpload, ExcelUpload
from .serializer import CargoSerializer, ProductoSerializer, IngresoSerializer, RetiroSerializer, UsuarioSerializer, \
    StockActualSerializer, ProductoStockSerializer, PDFUploadSerializer, ExcelUploadSerializer


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

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all()
    serializer_class = CargoSerializer
    permission_classes = [BodegueroNOT]

class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [BodegueroNOT]

class ProductoStockViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.select_related('stock').all()
    serializer_class = ProductoStockSerializer
    permission_classes = [BodegueroNOT]
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
    permission_classes = [BodegueroNOT]

class StockViewSet(viewsets.ModelViewSet):
    queryset = StockActual.objects.all()
    serializer_class = StockActualSerializer
    permission_classes = [BodegueroNOT]


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

                stock = StockActual.objects.get(producto_id=producto)
                stock.cantidad = int(row_data.get("Cantidad", 0))
                stock.save()



            response = ExcelUploadSerializer(excel_obj)
            excel_obj.delete()
            return Response(response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
