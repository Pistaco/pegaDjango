# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import os

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



class Cargo(models.Model):
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'cargo'

class Producto(models.Model):
    codigo_barras = models.CharField(unique=True, max_length=20)
    centro_costo = models.CharField(max_length=100, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    precio = models.IntegerField()
    parte = models.IntegerField(blank=True, null=True)



    class Meta:
        managed = True
        db_table = 'producto'

    def get_total(self):
        return sum(obj.precio for obj in Producto.objects.all())

class StockActual(models.Model):
    producto = models.OneToOneField(Producto, on_delete=models.CASCADE, related_name="stock")
    cantidad = models.IntegerField()
    actualizado_en = models.DateTimeField(auto_now=True)


class Ingreso(models.Model):
    id_producto = models.ForeignKey('Producto', models.CASCADE, db_column='id_producto')
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_column='id_usuario')
    cantidad = models.IntegerField()
    fecha = models.DateTimeField()
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ingreso'

class Retiro(models.Model):
    id_producto = models.ForeignKey(Producto, models.CASCADE, db_column='id_producto')
    id_usuario = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, db_column='id_usuario')
    cantidad = models.IntegerField()
    fecha = models.DateTimeField()
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
