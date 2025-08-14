# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
# Feel free to rename the models, but don't rename db_table values or field names.
import os
import uuid

from django.contrib.auth.models import User
from django.db import models

from django.conf import settings

class Familia(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    padre = models.ForeignKey(
        'self',
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name='subfamilias',
        help_text='Familia padre en caso de ser subcategoría.'
    )
    class Meta:
        db_table = 'familia'
        verbose_name = 'Familia'
        verbose_name_plural = 'Familias'

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

    class Meta:
        db_table = 'cargo'

class Producto(models.Model):
    codigo_barras = models.CharField(unique=True, max_length=20)
    centro_costo = models.CharField(max_length=100, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    precio = models.IntegerField()
    familia = models.ForeignKey(
        Familia,
        on_delete=models.CASCADE,
        related_name='productos',
        help_text='Familia o subfamilia a la que pertenece el producto.'
    )



    class Meta:
        db_table = 'producto'

    def save(self, *args, **kwargs):
        if not self.codigo_barras:
            self.codigo_barras = str(uuid.uuid4())[:20]
        super().save(*args, **kwargs)

    def get_total(self):
        return sum(obj.precio for obj in Producto.objects.all())

class Pendiente(models.Model):
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE, related_name='pendientes', db_column='producto_id')
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='pendientes', db_column='bodega_id')
    descripcion = models.TextField()
    completado = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pendiente'
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
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones', db_column='usuario_id')
    titulo = models.TextField()
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)
    stock = models.ForeignKey('StockActual', null=True, blank=True, on_delete=models.CASCADE,
                              related_name='notificaciones_stock', default=None)
    envio = models.ForeignKey('Envio', null=True, blank=True, on_delete=models.CASCADE, related_name='notificaciones_envio', default=None)
    pendiente = models.ForeignKey('Envio', null=True, blank=True, on_delete=models.CASCADE, related_name='notificaciones_pendiente', default=None)

    def __str__(self):
        return f"{self.titulo} - {'Leído' if self.leido else 'No leído'}"

    class Meta:
        db_table = 'notificacion'
        verbose_name = 'Notificación'

class Ingreso(models.Model):
    id_producto = models.ForeignKey('Producto', models.CASCADE, db_column='id_producto')
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_column='id_usuario')
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='ingresos')
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'ingreso'

class Retiro(models.Model):
    id_producto = models.ForeignKey(Producto, models.CASCADE, db_column='id_producto')
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_column='id_usuario')
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='retiros')
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'retiro'



class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password_hash = models.TextField()
    id_cargo = models.ForeignKey(Cargo, models.DO_NOTHING, db_column='id_cargo')
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'usuario'
    



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
        User,
        db_column='usuario_id',
        on_delete=models.PROTECT,
        related_name='envios'
    )

    class Meta:
        db_table = 'envio'

class EnvioDetalle(models.Model):
    envio = models.ForeignKey('Envio', on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    class Meta:
        db_table = 'envio_detalle'

class Bodega(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.TextField(blank=True)
    usuarios = models.ManyToManyField(User, related_name='bodegas', db_table='bodega_usuarios')

    class Meta:
        db_table = 'bodega'

class ImportJob(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.RESTRICT, db_column='usuario_id', related_name='import_jobs')
    bodega  = models.ForeignKey('Bodega', on_delete=models.RESTRICT, db_column='bodega_id', related_name='import_jobs')
    filename = models.TextField()
    total_rows = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')
    finished_at = models.DateTimeField(null=True, blank=True, db_column='finished_at')
    status = models.CharField(max_length=20, default='processing')
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'import_job'
        verbose_name = 'Importación'
        verbose_name_plural = 'Importaciones'

    def __str__(self):
        return f'Import #{self.id} - {self.filename} - {self.status}'


class ImportRow(models.Model):
    import_job = models.ForeignKey('ImportJob', on_delete=models.CASCADE, db_column='import_job_id', related_name='rows')
    row_number = models.IntegerField()
    nombre = models.TextField()
    cantidad = models.DecimalField(max_digits=18, decimal_places=4)
    precio = models.DecimalField(max_digits=18, decimal_places=2)
    producto = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True, blank=True, db_column='producto_id', related_name='import_rows')
    status = models.CharField(max_length=20, default='ok')
    message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'import_row'
        verbose_name = 'Fila importada'
        verbose_name_plural = 'Filas importadas'

    def __str__(self):
        return f'Row {self.row_number} ({self.status})'