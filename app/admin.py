from django.contrib import admin

from app.models import Pendiente


@admin.register(Pendiente)
class PendienteAdmin(admin.ModelAdmin):
    pass