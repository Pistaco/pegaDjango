from decimal import Decimal
import random

from django.contrib.auth.models import Group, User
from django.db import transaction

from app.models import (
    Bodega,
    Cargo,
    Envio,
    EnvioDetalle,
    Gerencia,
    ImportJob,
    ImportRow,
    Ingreso,
    Notificacion,
    Pendiente,
    Producto,
    Retiro,
    StockActual,
)

random.seed(42)
DUMMY_PREFIX = "DUMMY"


def barcode(i):
    return f"DMY{i:016d}"[:20]


@transaction.atomic
def seed_dummy():
    # Limpieza idempotente
    ImportRow.objects.filter(import_job__filename__startswith=f"{DUMMY_PREFIX}-").delete()
    ImportJob.objects.filter(filename__startswith=f"{DUMMY_PREFIX}-").delete()
    Notificacion.objects.filter(titulo__startswith=f"{DUMMY_PREFIX}-").delete()

    EnvioDetalle.objects.filter(envio__usuario__username__startswith="dummy_").delete()
    Envio.objects.filter(usuario__username__startswith="dummy_").delete()

    Retiro.objects.filter(usuario__username__startswith="dummy_").delete()
    Ingreso.objects.filter(usuario__username__startswith="dummy_").delete()
    Pendiente.objects.filter(descripcion__startswith=f"{DUMMY_PREFIX}-").delete()

    StockActual.objects.filter(producto__nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    Producto.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    Gerencia.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()

    Bodega.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    Cargo.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").delete()
    User.objects.filter(username__startswith="dummy_").delete()

    # Grupos
    g_bod, _ = Group.objects.get_or_create(name="Bodeguero")
    g_admin, _ = Group.objects.get_or_create(name="Admin")

    # Cargos
    for n in ["Bodeguero", "Supervisor", "Compras"]:
        Cargo.objects.get_or_create(
            nombre=f"{DUMMY_PREFIX}-{n}",
            defaults={"descripcion": f"Cargo {n} dummy"},
        )

    # Usuarios
    users = []
    for i in range(1, 7):
        u = User.objects.create_user(
            username=f"dummy_user_{i}",
            email=f"dummy_user_{i}@example.com",
            password="dummy12345",
        )
        if i <= 4:
            u.groups.add(g_bod)
        else:
            u.groups.add(g_admin)
        users.append(u)

    # Bodegas
    bodegas = []
    for i in range(1, 4):
        b = Bodega.objects.create(
            nombre=f"{DUMMY_PREFIX}-Bodega-{i}",
            ubicacion=f"Zona {i}",
        )
        bodegas.append(b)

    bodegas[0].usuarios.add(users[0], users[1], users[4])
    bodegas[1].usuarios.add(users[1], users[2], users[5])
    bodegas[2].usuarios.add(users[0], users[3], users[4])

    # Gerencias
    g_ops = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-Operaciones")
    g_mant = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-Mantenimiento", padre=g_ops)
    g_seg = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-Seguridad", padre=g_ops)
    g_ti = Gerencia.objects.create(nombre=f"{DUMMY_PREFIX}-TI")
    gerencias = [g_ops, g_mant, g_seg, g_ti]

    # Productos
    productos = []
    for i in range(1, 31):
        p = Producto.objects.create(
            codigo_barras=barcode(i),
            centro_costo=f"CC-{1000 + i}",
            nombre=f"{DUMMY_PREFIX}-Producto-{i:02d}",
            descripcion=f"Producto de prueba {i}",
            precio=random.randint(1000, 20000),
            parte=random.randint(10000, 99999),
            gerencia=random.choice(gerencias),
        )
        productos.append(p)

    # Stock
    stock_rows = []
    for p in productos:
        for b in bodegas:
            if random.random() < 0.75:
                stock_rows.append(
                    StockActual(
                        producto=p,
                        bodega=b,
                        cantidad=random.randint(0, 80),
                    )
                )
    StockActual.objects.bulk_create(stock_rows, ignore_conflicts=True)

    # Ingresos
    for _ in range(40):
        p = random.choice(productos)
        b = random.choice(bodegas)
        u = random.choice(users[:4])
        qty = random.randint(1, 20)

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

    # Retiros
    for _ in range(25):
        p = random.choice(productos)
        b = random.choice(bodegas)
        u = random.choice(users[:4])
        qty = random.randint(1, 15)
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
    for i in range(1, 16):
        Pendiente.objects.create(
            producto=random.choice(productos),
            bodega=random.choice(bodegas),
            descripcion=f"{DUMMY_PREFIX}-Pendiente-{i}",
            completado=(i % 4 == 0),
        )

    # Envios y detalles (dispara signal de notificaciones)
    for i in range(1, 11):
        bo, bd = random.sample(bodegas, 2)
        e = Envio.objects.create(
            bodega_origen=bo,
            bodega_destino=bd,
            usuario=random.choice(users),
            confirmado=(i % 3 == 0),
        )
        for _ in range(random.randint(1, 4)):
            EnvioDetalle.objects.create(
                envio=e,
                producto=random.choice(productos),
                cantidad=random.randint(1, 10),
            )

    # Notificaciones manuales extra
    for i in range(1, 11):
        Notificacion.objects.create(
            usuario=random.choice(users),
            titulo=f"{DUMMY_PREFIX}-Notificacion-{i}",
            mensaje="Mensaje de prueba",
            leido=(i % 2 == 0),
        )

    # Importaciones dummy
    for j in range(1, 4):
        job = ImportJob.objects.create(
            usuario=random.choice(users),
            bodega=random.choice(bodegas),
            filename=f"{DUMMY_PREFIX}-archivo-{j}.xlsx",
            total_rows=10,
            status="done",
        )
        rows = []
        for r in range(1, 11):
            pr = random.choice(productos)
            rows.append(
                ImportRow(
                    import_job=job,
                    row_number=r,
                    nombre=pr.nombre,
                    cantidad=Decimal(str(random.randint(1, 20))),
                    precio=Decimal(str(pr.precio)),
                    producto=pr,
                    status="ok",
                    message="OK",
                )
            )
        ImportRow.objects.bulk_create(rows)

    print("Seed dummy completado")
    print("Usuarios:", User.objects.filter(username__startswith="dummy_").count())
    print("Bodegas:", Bodega.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").count())
    print("Gerencias:", Gerencia.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").count())
    print("Productos:", Producto.objects.filter(nombre__startswith=f"{DUMMY_PREFIX}-").count())


if __name__ == "__main__":
    seed_dummy()
