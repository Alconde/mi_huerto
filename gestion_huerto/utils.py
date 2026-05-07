from datetime import timedelta
from django.utils import timezone

from .models import Plantacion


FAMILIAS_SENSIBLES = {
    'solanaceas': 'Solanáceas',
    'cucurbitaceas': 'Cucurbitáceas',
    'cruciferas': 'Crucíferas',
    'hoja': 'Hoja',
    'umbeliferas': 'Umbelíferas',
    'leguminosas': 'Leguminosas',
    'aliaceas': 'Aliáceas',
    'gramineas': 'Gramíneas',
    'compuestas': 'Compuestas',
    'otros': 'Otros',
}


MESES_ALERTA_FAMILIA = {
    'solanaceas': 36,
    'cucurbitaceas': 24,
    'cruciferas': 24,
    'umbeliferas': 24,
    'aliaceas': 18,
    'leguminosas': 12,
    'hoja': 12,
    'gramineas': 12,
    'compuestas': 18,
    'otros': 12,
}


def hay_solape_rango(a_inicio, a_fin, b_inicio, b_fin):
    return a_inicio <= b_fin and b_inicio <= a_fin


def misma_zona(parcela, fila_inicio, fila_fin, columna_inicio, columna_fin, otra):
    if parcela != otra.parcela:
        return False

    solape_filas = hay_solape_rango(fila_inicio, fila_fin, otra.fila_inicio, otra.fila_fin)
    solape_columnas = hay_solape_rango(columna_inicio, columna_fin, otra.columna_inicio, otra.columna_fin)

    return solape_filas and solape_columnas


def obtener_familia_codigo(plantacion):
    if plantacion and plantacion.cultivo and plantacion.cultivo.familia:
        return plantacion.cultivo.familia
    return None


def obtener_familia_label(plantacion):
    if plantacion and plantacion.cultivo:
        return plantacion.cultivo.get_familia_display()
    return "Familia desconocida"


def obtener_fecha_referencia(plantacion):
    return (
        plantacion.fecha_recoleccion_inicio
        or plantacion.fecha_trasplante
        or plantacion.fecha_siembra
    )


def buscar_warning_rotacion(plantacion):
    if not plantacion or not plantacion.cultivo or not plantacion.parcela:
        return None

    if plantacion.cultivo.es_perenne:
        return None

    familia_actual = obtener_familia_codigo(plantacion)
    if not familia_actual:
        return None

    meses_alerta = MESES_ALERTA_FAMILIA.get(familia_actual, 12)
    hoy = timezone.localdate()
    fecha_limite = hoy - timedelta(days=meses_alerta * 30)

    plantaciones_anteriores = (
        Plantacion.objects
        .filter(parcela=plantacion.parcela)
        .exclude(pk=plantacion.pk)
        .select_related('cultivo', 'parcela')
        .order_by('-fecha_siembra')
    )

    coincidencias = []

    for anterior in plantaciones_anteriores:
        if not anterior.cultivo:
            continue

        if anterior.cultivo.es_perenne:
            continue

        familia_anterior = obtener_familia_codigo(anterior)
        if familia_anterior != familia_actual:
            continue

        if not misma_zona(
            plantacion.parcela,
            plantacion.fila_inicio,
            plantacion.fila_fin,
            plantacion.columna_inicio,
            plantacion.columna_fin,
            anterior
        ):
            continue

        fecha_referencia = obtener_fecha_referencia(anterior)
        if not fecha_referencia:
            continue

        if fecha_referencia >= fecha_limite:
            coincidencias.append(anterior)

    if not coincidencias:
        return None

    anterior = coincidencias[0]
    familia_label = obtener_familia_label(plantacion)

    return (
        f"Aviso de rotación: estás repitiendo la familia {familia_label} "
        f"en la misma zona de la parcela {plantacion.parcela.nombre}. "
        f"Se ha detectado una plantación reciente de {anterior.cultivo.nombre}. "
        f"En horticultura ecológica conviene dejar más tiempo antes de repetir "
        f"la misma familia para reducir presión de plagas y enfermedades del suelo."
    )