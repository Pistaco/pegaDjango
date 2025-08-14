from django.contrib import admin
from django.contrib.admin import AdminSite

from app.models import Producto, Ingreso, Retiro, StockActual, PDFUpload, ExcelUpload, Bodega, Envio, EnvioDetalle, \
    Notificacion, Pendiente, ImportJob, ImportRow


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


@admin.register(Bodega)
class Bodegaadmin(admin.ModelAdmin):
    pass


@admin.register(Envio)
class EnvioAdmin(admin.ModelAdmin):
    pass


@admin.register(EnvioDetalle)
class EnvioDetalleAdmin(admin.ModelAdmin):
    pass


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    pass


@admin.register(Pendiente)
class PendienteAdmin(admin.ModelAdmin):
    pass


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    pass

@admin.register(ImportRow)
class ImportRowAdmin(admin.ModelAdmin):
    pass