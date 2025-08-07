# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import os
import uuid

from django.contrib.auth.models import User
from django.db import models

from django.conf import settings


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)




class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'

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
        managed = False
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
        managed = False
        db_table = 'cargo'

class Producto(models.Model):
    codigo_barras = models.CharField(unique=True, max_length=20, default=str(uuid.uuid4())[:20])
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
        managed = True
        db_table = 'producto'

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
    stock = models.ForeignKey('StockActual', null=True, blank=True, on_delete=models.SET_NULL,
                              related_name='notificaciones_stock', default=None)
    envio = models.ForeignKey('Envio', null=True, blank=True, on_delete=models.SET_NULL, related_name='notificaciones_envio', default=None)
    pendiente = models.ForeignKey('Envio', null=True, blank=True, on_delete=models.SET_NULL, related_name='notificaciones_pendiente', default=None)

    def __str__(self):
        return f"{self.titulo} - {'Leído' if self.leido else 'No leído'}"

    class Meta:
        managed = False
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
        managed = False
        db_table = 'ingreso'

class Retiro(models.Model):
    id_producto = models.ForeignKey(Producto, models.CASCADE, db_column='id_producto')
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_column='id_usuario')
    bodega = models.ForeignKey('Bodega', on_delete=models.CASCADE, related_name='retiros')
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now=True)
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'retiro'



class Usuario(models.Model):
    nombre = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    password_hash = models.TextField()
    id_cargo = models.ForeignKey(Cargo, models.DO_NOTHING, db_column='id_cargo')
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
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

    class Meta:
        managed = False
        db_table = 'envio'

class EnvioDetalle(models.Model):
    envio = models.ForeignKey('Envio', on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'envio_detalle'

class Bodega(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.TextField(blank=True)
    usuarios = models.ManyToManyField(User, related_name='bodegas', db_table='bodega_usuarios')

    class Meta:
        managed = False
        db_table = 'bodega'
