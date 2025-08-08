from django.contrib import admin
from django.contrib.admin import AdminSite

from app.models import Producto, Ingreso, Retiro, StockActual, PDFUpload, ExcelUpload


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    pass

@admin.register(StockActual)
class StockActualAdmin(admin.ModelAdmin):
    pass

@admin.register(Ingreso)
class IngresoAdmin(admin.ModelAdmin):
    pass


@admin.register(Retiro)
class RetiroAdmin(admin.ModelAdmin):
    pass


class BodegueroAdminSite(AdminSite):
    site_header = "Panel de Bodeguero"

    def has_permission(self, request):
        return request.user.is_authenticated and request.user.groups.filter(name="Bodeguero").exists()

bodeguero_admin_site = BodegueroAdminSite(name='admin_bodeguero')
bodeguero_admin_site.register(Ingreso)
bodeguero_admin_site.register(Retiro)


@admin.register(PDFUpload)
class PDFUploadAdmin(admin.ModelAdmin):
    pass


@admin.register(ExcelUpload)
class ExcelUploadAdmin(admin.ModelAdmin):
    pass