from decimal import Decimal
import random
from uuid import uuid4

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.db import transaction

from app.models import (
    Bodega,
    Cargo,
    Envio,
    EnvioDetalle,
    ExcelUpload,
    Gerencia,
    ImportJob,
    ImportRow,
    Ingreso,
    Notificacion,
    PDFUpload,
    Pendiente,
    Producto,
    Retiro,
    StockActual,
    Usuario,
)

random.seed(123)
DUMMY_PREFIX = "DUMMY2"


def barcode(i):
    return f"D2{i:018d}"[:20]


@transaction.atomic
def seed_dummy_stocks_completo():
    # Limpieza idempotente
    ImportRow.objects.filter(import_job__filename__startswith=f"{DUMMY_PREFIX}-").delete()
    ImportJob.objects.filter(filename__startswith=f"{DUMMY_PREFIX}-").delete()
    Notificacion.objects.filter(titulo__startswith=f"{DUMMY_PREFIX}-").delete()

    EnvioDetalle.objects.filter(envio__usuario__username__startswith="dummy2_").delete()
    Envio.objects.filter(usuario__username__startswith="dummy2_").delete()

    Retiro.objects.filter(usuario__username__startswith="dummy2_").delete()
    Ingreso.objects.filter(usuario__username__startswith="dummy2_").delete()
    Pendiente.objects.filter(descripcion__startswith=f"{DUMMY_PREFIX}-").delete()

    StockActual.objects.filter(producto__nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    Producto.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    Gerencia.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()

    Bodega.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    Usuario.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    Cargo.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    User.objects.filter(username__startswith="dummy2_").delete()
    PDFUpload.objects.filter(archivo__startswith="pdfs/dummy2_").delete()
    ExcelUpload.objects.filter(archivo__startswith="excels/dummy2_").delete()

    # Grupos
    g_bod, _ = Group.objects.get_or_create(name="Bodeguero")
    g_admin, _ = Group.objects.get_or_create(name="Admin")

    # Cargos (incluye para modelo Usuario legacy)
    cargos = []
    for n in ["Bodeguero", "Supervisor", "Compras", "Analista"]:
        c, _ = Cargo.objects.get_or_create(
            nombre=f"{DUMMY_PREFIX}-{n}",
            defaults={"descripcion": f"Cargo {n} dummy"},
        )
        cargos.append(c)

    # Usuarios auth
    users = []
    for i in range(1, 9):
        u = User.objects.create_user(
            username=f"dummy2_user_{i}",
            email=f"dummy2_user_{i}@example.com",
            password="dummy12345",
        )
        if i <= 5:
            u.groups.add(g_bod)
        else:
            u.groups.add(g_admin)
        users.append(u)

    # Usuarios legacy
    for i in range(1, 6):
        Usuario.objects.create(
            nombre=f"{DUMMY_PREFIX}-UsuarioLegacy-{i}",
            email=f"dummy2_legacy_{i}@example.com",
            password_hash=f"hash_dummy_{i}",
            cargo=random.choice(cargos),
        )

    # Bodegas
    bodegas = []
    for i in range(1, 5):
        b = Bodega.objects.create(
            nombre=f"{DUMMY_PREFIX}-Bodega-{i}",
            ubicacion=f"Sector {i}",
        )
        bodegas.append(b)

    bodegas[0].usuarios.add(users[0], users[1], users[5])
    bodegas[1].usuarios.add(users[1], users[2], users[6])
    bodegas[2].usuarios.add(users[2], users[3], users[7])
    bodegas[3].usuarios.add(users[0], users[4], users[5], users[6])

    # Gerencias
    g_ops = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-Operaciones")
    g_log = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-Logistica", padre=g_ops)
    g_mant = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-Mantenimiento", padre=g_ops)
    g_ti = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-TI")
    g_adm = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-Administracion")
    gerencias = [g_ops, g_log, g_mant, g_ti, g_adm]

    # Productos
    productos = []
    for i in range(1, 61):
        p = Producto.objects.create(
            codigo_barras=barcode(i),
            centro_costo=f"CC2-{2000 + i}",
            nombre=f"{DUMMY_PREFIX}-Producto-{i:03d}",
            descripcion=f"Producto dummy completo {i}",
            precio=random.randint(1500, 50000),
            parte=random.randint(10000, 99999),
            gerencia=random.choice(gerencias),
        )
        productos.append(p)

    # Stock completo (todos los productos en todas las bodegas)
    stock_rows = []
    for p in productos:
        for idx, b in enumerate(bodegas):
            if idx == 0:
                qty = random.randint(25, 120)   # alta rotacion
            elif idx == 1:
                qty = random.randint(5, 40)     # media
            elif idx == 2:
                qty = random.randint(1, 8)      # bajo stock frecuente
            else:
                qty = random.randint(0, 15)     # mixto, incluye cero
            stock_rows.append(StockActual(producto=p, bodega=b, cantidad=qty))
    StockActual.objects.bulk_create(stock_rows, ignore_conflicts=True)

    # Ingresos y Retiros
    for _ in range(80):
        p = random.choice(productos)
        b = random.choice(bodegas)
        u = random.choice(users[:5])
        qty = random.randint(1, 25)

        Ingreso.objects.create(
            producto=p,
            bodega=b,
            usuario=u,
            cantidad=qty,
            observacion=f"{DUMMY_PREFIX}-Ingreso",
        )
        s, _ = StockActual.objects.get_or_create(producto=p, bodega=b, defaults={"cantidad": 0})
        s.cantidad += qty
        s.save(update_fields=["cantidad", "actualizado_en"])

    for _ in range(55):
        p = random.choice(productos)
        b = random.choice(bodegas)
        u = random.choice(users[:5])
        qty = random.randint(1, 20)
        s = StockActual.objects.filter(producto=p, bodega=b).first()
        if not s or s.cantidad < qty:
            continue

        Retiro.objects.create(
            producto=p,
            bodega=b,
            usuario=u,
            cantidad=qty,
            observacion=f"{DUMMY_PREFIX}-Retiro",
        )
        s.cantidad -= qty
        if s.cantidad == 0:
            s.delete()
        else:
            s.save(update_fields=["cantidad", "actualizado_en"])

    # Pendientes
    for i in range(1, 31):
        Pendiente.objects.create(
            producto=random.choice(productos),
            bodega=random.choice(bodegas),
            descripcion=f"{DUMMY_PREFIX}-Pendiente-{i}",
            completado=(i % 5 == 0),
        )

    # Envios
    for i in range(1, 21):
        bo, bd = random.sample(bodegas, 2)
        envio = Envio.objects.create(
            bodega_origen=bo,
            bodega_destino=bd,
            usuario=random.choice(users),
            confirmado=(i % 4 == 0),
        )
        for _ in range(random.randint(1, 5)):
            EnvioDetalle.objects.create(
                envio=envio,
                producto=random.choice(productos),
                cantidad=random.randint(1, 12),
            )

    # Notificaciones extra
    stock_list = list(StockActual.objects.filter(producto__nombre__startswith=f"{DUMMY_PREFIX}-")[:30])
    pendiente_list = list(Pendiente.objects.filter(descripcion__startswith=f"{DUMMY_PREFIX}-")[:15])
    envio_list = list(Envio.objects.filter(usuario__username__startswith="dummy2_")[:15])
    for i in range(1, 21):
        n = Notificacion.objects.create(
            usuario=random.choice(users),
            titulo=f"{DUMMY_PREFIX}-Notificacion-{i}",
            mensaje=f"Notificacion dummy #{i}",
            leido=(i % 3 == 0),
        )
        # Asocia a una sola entidad (como regla del serializer)
        mod = i % 3
        if mod == 0 and stock_list:
            n.stock = random.choice(stock_list)
        elif mod == 1 and envio_list:
            n.envio = random.choice(envio_list)
        elif pendiente_list:
            n.pendiente = random.choice(pendiente_list)
        n.save()

    # Importaciones dummy
    for j in range(1, 5):
        job = ImportJob.objects.create(
            usuario=random.choice(users),
            bodega=random.choice(bodegas),
            filename=f"{DUMMY_PREFIX}-archivo-{j}.xlsx",
            total_rows=15,
            status="done",
        )
        rows = []
        for r in range(1, 16):
            pr = random.choice(productos)
            rows.append(
                ImportRow(
                    import_job=job,
                    row_number=r,
                    nombre=pr.nombre,
                    cantidad=Decimal(str(random.randint(1, 30))),
                    precio=Decimal(str(pr.precio)),
                    producto=pr,
                    status="ok",
                    message="OK",
                )
            )
        ImportRow.objects.bulk_create(rows)

    # PDF/Excel uploads dummy (archivos minimos)
    for i in range(1, 4):
        pdf = PDFUpload()
        pdf.archivo.save(
            f"dummy2_{uuid4().hex[:8]}_{i}.pdf",
            ContentFile(b"%PDF-1.1\n1 0 obj <<>>\nendobj\ntrailer <<>>\n%%EOF\n"),
            save=True,
        )
        xls = ExcelUpload()
        xls.archivo.save(
            f"dummy2_{uuid4().hex[:8]}_{i}.csv",
            ContentFile(b"nombre,cantidad,precio\nproducto,1,1000\n"),
            save=True,
        )

    print("Seed dummy completo de stocks finalizado")
    print("Users auth:", User.objects.filter(username__startswith="dummy2_").count())
    print("Usuarios legacy:", Usuario.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").count())
    print("Bodegas:", Bodega.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").count())
    print("Gerencias:", Gerencia.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").count())
    print("Productos:", Producto.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").count())
    print("Stocks:", StockActual.objects.filter(producto__nombre__startswith=f"{DUMMY_PREFIX}-").count())


if __name__ == "__main__":
    seed_dummy_stocks_completo()
