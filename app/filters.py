# app/filters.py
import django_filters
from django.db.models import Q, Exists, OuterRef
from .models import StockActual, Bodega, Producto, Familia  # ajusta nombres si difieren
from django.db import connection
from django_filters import rest_framework as filters

class StockFilter(django_filters.FilterSet):
    # Rango de cantidad
    cantidad_min = django_filters.NumberFilter(field_name="cantidad", lookup_expr="gte")
    cantidad_max = django_filters.NumberFilter(field_name="cantidad", lookup_expr="lte")

    # Filtros directos
    bodega = django_filters.ModelChoiceFilter(field_name="bodega", queryset=Bodega.objects.all())
    producto = django_filters.ModelChoiceFilter(field_name="producto", queryset=Producto.objects.all())

    # Búsqueda libre (q)
    q = django_filters.CharFilter(method="filter_q")

    def filter_q(self, queryset, name, value):
        # Ajusta los campos de búsqueda según tu modelo
        return queryset.filter(
            Q(producto__nombre__icontains=value) |
            Q(producto__codigo_barras__icontains=value) |
            Q(bodega__nombre__icontains=value)
        )

    class Meta:
        model = StockActual
        fields = ["bodega", "producto", "cantidad_min", "cantidad_max", "q"]

# app/filters.py

# Ajusta el nombre de la tabla y de las columnas si difieren en tu esquema real.
# Asumo una tabla 'familia' con columnas: id, nombre, padre_id (FK a familia.id).

class FamiliaFilterSet(filters.FilterSet):
    # hijos directos
    hijos_de = filters.NumberFilter(method='filter_hijos_de')
    # subárbol de un padre (todos los descendientes)
    subtree_of = filters.NumberFilter(method='filter_subtree_of')
    include_self = filters.BooleanFilter(method='filter_include_self', label='Include self')

    def _get_subtree_ids(self, parent_id: int, include_self: bool = False):
        """
        Obtiene IDs del subárbol vía CTE recursivo en PostgreSQL.
        No requiere cambios en el modelo ni en el serializer.
        """
        with connection.cursor() as cur:
            cur.execute(
                """
                WITH RECURSIVE subarbol AS (
                    SELECT id, padre_id
                    FROM familia
                    WHERE id = %s
                    UNION ALL
                    SELECT f.id, f.padre_id
                    FROM familia f
                    JOIN subarbol s ON f.padre_id = s.id
                )
                SELECT id FROM subarbol;
                """,
                [parent_id],
            )
            ids = [row[0] for row in cur.fetchall()]

        if not include_self:
            # Excluir el propio padre
            try:
                ids.remove(parent_id)
            except ValueError:
                pass
        return ids

    def filter_hijos_de(self, queryset, name, value):
        # Solo hijos directos: padre_id = value
        return queryset.filter(**{'padre_id': value})

    def filter_subtree_of(self, queryset, name, value):
        include_self = bool(self.data.get('include_self'))  # "1", "true" → True
        ids = self._get_subtree_ids(value, include_self=include_self)
        if not ids:
            return queryset.none()
        return queryset.filter(id__in=ids)

    def filter_include_self(self, queryset, name, value):
        # Este filtro no altera por sí solo; sirve como flag leído por filter_subtree_of
        return queryset

    class Meta:
        # Ajusta 'Familia' al nombre real de tu modelo
        model = Familia
        fields = ['hijos_de', 'subtree_of', 'include_self']

# filters.py

class BodegaFilter(django_filters.FilterSet):
    # el frontend enviará ?producto=<id>
    producto = django_filters.NumberFilter(method='filter_por_producto')

    class Meta:
        model = Bodega
        fields = ['producto']

    def filter_por_producto(self, queryset, name, value):
        subq = StockActual.objects.filter(
            bodega_id=OuterRef('pk'),
            producto_id=value,
            cantidad__gt=0
        )
        return queryset.filter(Exists(subq))
