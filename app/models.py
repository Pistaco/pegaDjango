import os
import uuid

from django.conf import settings
from django.db import models

class Gerencia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    padre = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='subgerencias',
        help_text='Gerencia padre en caso de ser subcategoría.'
    )
    class Meta:
        verbose_name = 'Gerencia'
        verbose_name_plural = 'Gerencias'

    def __str__(self):
        return self.nombre

    def get_ruta_completa(self):
        ruta = [self.nombre]
        padre = self.padre
        while padre:
            ruta.insert(0, padre.nombre)
            padre = padre.padre
        return " > ".join(ruta)

    def __str__(self):
        return self.nombre


class Cargo(models.Model):
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.TextField(blank=True, null=True)

class Producto(models.Model):
    codigo_barras = models.CharField(unique=True, max_length=20)
    centro_costo = models.CharField(max_length=100, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    precio = models.IntegerField()
    parte = models.IntegerField(blank=True, null=True)
    gerencia = models.ForeignKey(
        Gerencia,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='productos',
        help_text='Gerencia o subgerencia a la que pertenece el producto.'
    )

    def save(self, *args, **kwargs):
        if not self.codigo_barras:
            self.codigo_barras = str(uuid.uuid4())[:20]
        super().save(*args, **kwargs)

    def get_total(self):
        return sum(obj.precio for obj in Producto.objects.all())

class Pendiente(models.Model):
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='pendientes')
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='pendientes')
    descripcion = models.TextField()
    completado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pendiente'
        verbose_name_plural = 'Pendientes'
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.descripcion} ({'completado' if self.completado else 'pendiente'})"


class StockActual(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="stock")
    cantidad = models.IntegerField()
    actualizado_en = models.DateTimeField(auto_now=True)
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name="stock")

    class Meta:
        unique_together = ('producto', 'bodega')


class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificaciones')
    titulo = models.TextField()
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)
    stock = models.ForeignKey('StockActual', null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='notificaciones_stock', default=None)
    envio = models.ForeignKey('Envio', null=True, blank=True, on_delete=models.CASCADE, related_name='notificaciones_envio', default=None)
    pendiente = models.ForeignKey('Pendiente', null=True, blank=True, on_delete=models.CASCADE, related_name='notificaciones_pendiente', default=None)

    def __str__(self):
        return f"{self.titulo} - {'Leído' if self.leido else 'No leído'}"

    class Meta:
        verbose_name = 'Notificación'

class Ingreso(models.Model):
    producto = models.ForeignKey('Producto', models.CASCADE, related_name='ingresos')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, related_name='ingresos')
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='ingresos')
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)

class Retiro(models.Model):
    producto = models.ForeignKey(Producto, models.CASCADE, related_name='retiros')
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, related_name='retiros')
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='retiros')
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now=True)
    observacion = models.TextField(blank=True, null=True)



class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password_hash = models.TextField()
    cargo = models.ForeignKey(Cargo, models.DO_NOTHING)
    created_at = models.DateTimeField(blank=True, null=True)

class PDFUpload(models.Model):
    archivo = models.FileField(upload_to='pdfs/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    def delete(self, *args, **kwargs):
        if self.archivo:
            if os.path.isfile(self.archivo.path):
                os.remove(self.archivo.path)
        super().delete(*args, **kwargs)

class ExcelUpload(models.Model):
    archivo = models.FileField(upload_to='excels/')
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def delete(self, *args, **kwargs):
        if self.archivo:
            if os.path.isfile(self.archivo.path):
                os.remove(self.archivo.path)
        super().delete(*args, **kwargs)


class Envio(models.Model):
    bodega_origen = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='envios_salientes')
    bodega_destino = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='envios_entrantes')
    fecha = models.DateTimeField(auto_now_add=True)
    confirmado = models.BooleanField(default=False)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='envios'
    )

class EnvioDetalle(models.Model):
    envio = models.ForeignKey('Envio', on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

class Bodega(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.TextField(blank=True)
    usuarios = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='bodegas')

class ImportJob(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name='import_jobs')
    bodega  = models.ForeignKey('Bodega', on_delete=models.RESTRICT, related_name='import_jobs')
    filename = models.TextField()
    total_rows = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, default='processing')
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Importación'
        verbose_name_plural = 'Importaciones'

    def __str__(self):
        return f'Import #{self.id} - {self.filename} - {self.status}'


class ImportRow(models.Model):
    import_job = models.ForeignKey('ImportJob', on_delete=models.CASCADE, related_name='rows')
    row_number = models.IntegerField()
    nombre = models.TextField()
    cantidad = models.DecimalField(max_digits=18, decimal_places=4)
    precio = models.DecimalField(max_digits=18, decimal_places=2)
    producto = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True, blank=True, related_name='import_rows')
    status = models.CharField(max_length=20, default='ok')
    message = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Fila importada'
        verbose_name_plural = 'Filas importadas'

    def __str__(self):
        return f'Row {self.row_number} ({self.status})'
