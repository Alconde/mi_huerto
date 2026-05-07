from datetime import timedelta, date
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, OuterRef, Subquery, Sum, Count
from .models import *
from .forms import *
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView
from collections import Counter, OrderedDict, defaultdict
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.contrib import messages
from .utils import buscar_warning_rotacion
from itertools import chain
from operator import attrgetter
from decimal import Decimal



def dashboard(request):
    hoy = timezone.now().date()

    total_plantaciones = Plantacion.objects.count()
    tareas_recientes = Tarea.objects.order_by('-fecha')[:5]

    ultimo_riego_subquery = Tarea.objects.filter(
        plantacion=OuterRef('pk'),
        tipo='riego'
    ).order_by('-fecha').values('fecha')[:1]

    plantaciones_con_riego = Plantacion.objects.annotate(
        ultimo_riego=Subquery(ultimo_riego_subquery)
    )

    riego_verde = 0
    riego_amarillo = 0
    riego_rojo = 0
    riego_gris = 0

    for plantacion in plantaciones_con_riego:
        if not plantacion.ultimo_riego:
            riego_gris += 1
            continue

        dias_sin_riego = (hoy - plantacion.ultimo_riego).days

        if dias_sin_riego < 6:
            riego_verde += 1
        elif 7 <= dias_sin_riego <= 10:
            riego_amarillo += 1
        elif dias_sin_riego > 10:
            riego_rojo += 1
        else:
            riego_gris += 1

    total_remedios = RemedioBotica.objects.filter(activo=True).count()

    aplicaciones_recientes = AplicacionRemedio.objects.select_related(
        'remedio',
        'cultivo',
        'parcela',
        'tarea_seguimiento'
    ).order_by('-fecha_aplicacion')[:5]

    seguimientos_pendientes = AplicacionRemedio.objects.filter(
        tarea_seguimiento__isnull=False,
        tarea_seguimiento__completada=False
    ).select_related(
        'remedio',
        'tarea_seguimiento'
    ).order_by('tarea_seguimiento__fecha_proxima', 'tarea_seguimiento__fecha')[:5]

    total_seguimientos_pendientes = AplicacionRemedio.objects.filter(
        tarea_seguimiento__isnull=False,
        tarea_seguimiento__completada=False
    ).count()

    context = {
        'total_plantaciones': total_plantaciones,
        'tareas_recientes': tareas_recientes,
        'riego_verde': riego_verde,
        'riego_amarillo': riego_amarillo,
        'riego_rojo': riego_rojo,
        'riego_gris': riego_gris,
        'total_remedios': total_remedios,
        'aplicaciones_recientes': aplicaciones_recientes,
        'seguimientos_pendientes': seguimientos_pendientes,
        'total_seguimientos_pendientes': total_seguimientos_pendientes,
    }

    return render(request, 'dashboard.html', context)


def lista_cultivos(request):
    tipo = request.GET.get('tipo')  # puede ser 'hortaliza', 'frutal', 'flor' o None

    cultivos = Cultivo.objects.all().order_by('nombre')

    if tipo in ['hortaliza', 'frutal', 'flor']:
        cultivos = cultivos.filter(tipo_cultivo=tipo)

    contexto = {
        'cultivos': cultivos,
        'tipo_seleccionado': tipo,
    }
    return render(request, 'cultivos/lista.html', contexto)


def detalle_cultivo(request, cultivo_id):
    cultivo = get_object_or_404(Cultivo, pk=cultivo_id)
    return render(request, 'cultivos/detalle.html', {'cultivo': cultivo})


def editar_cultivo(request, cultivo_id=None):
    if cultivo_id:
        cultivo = get_object_or_404(Cultivo, pk=cultivo_id)
    else:
        cultivo = None

    ficha_frutal = None
    ficha_flor = None
    if cultivo:
        ficha_frutal = getattr(cultivo, 'ficha_frutal', None)
        ficha_flor = getattr(cultivo, 'ficha_flor', None)

    if request.method == 'POST':
        cultivo_form = CultivoForm(request.POST, instance=cultivo)

        tipo_cultivo = request.POST.get('tipo_cultivo')

        ficha_frutal_form = FichaFrutalForm(
            request.POST,
            instance=ficha_frutal,
            prefix='frutal'
        )
        ficha_flor_form = FichaFlorForm(
            request.POST,
            instance=ficha_flor,
            prefix='flor'
        )

        formularios_validos = cultivo_form.is_valid()

        if tipo_cultivo == 'frutal':
            formularios_validos = formularios_validos and ficha_frutal_form.is_valid()
        elif tipo_cultivo == 'flor':
            formularios_validos = formularios_validos and ficha_flor_form.is_valid()

        if formularios_validos:
            cultivo = cultivo_form.save()

            if tipo_cultivo == 'frutal':
                ficha = ficha_frutal_form.save(commit=False)
                ficha.cultivo = cultivo
                ficha.save()
                if hasattr(cultivo, 'ficha_flor'):
                    cultivo.ficha_flor.delete()

            elif tipo_cultivo == 'flor':
                ficha = ficha_flor_form.save(commit=False)
                ficha.cultivo = cultivo
                ficha.save()
                if hasattr(cultivo, 'ficha_frutal'):
                    cultivo.ficha_frutal.delete()

            else:
                if hasattr(cultivo, 'ficha_frutal'):
                    cultivo.ficha_frutal.delete()
                if hasattr(cultivo, 'ficha_flor'):
                    cultivo.ficha_flor.delete()

            messages.success(request, 'Cultivo guardado correctamente.')
            return redirect('lista_cultivos')
    else:
        cultivo_form = CultivoForm(instance=cultivo)
        ficha_frutal_form = FichaFrutalForm(
            instance=ficha_frutal,
            prefix='frutal'
        )
        ficha_flor_form = FichaFlorForm(
            instance=ficha_flor,
            prefix='flor'
        )

    return render(request, 'cultivos/formulario.html', {
        'form': cultivo_form,
        'ficha_frutal_form': ficha_frutal_form,
        'ficha_flor_form': ficha_flor_form,
        'cultivo': cultivo,
    })

def eliminar_cultivo(request, cultivo_id):
    cultivo = get_object_or_404(Cultivo, pk=cultivo_id)
    if request.method == 'POST':
        cultivo.delete()
        messages.success(request, 'Cultivo eliminado correctamente.')
        return redirect('lista_cultivos')
    return render(request, 'cultivos/confirmar_borrado.html', {'cultivo': cultivo})

def lista_variedades(request):
    variedades = Variedad.objects.all()
    return render(request, 'variedades/lista.html', {'variedades': variedades})

def editar_variedad(request, variedad_id=None):
    if variedad_id:
        variedad = get_object_or_404(Variedad, pk=variedad_id)
    else:
        variedad = None
    if request.method == 'POST':
        form = VariedadForm(request.POST, instance=variedad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Variedad guardada correctamente.')
            return redirect('lista_variedades')
    else:
        form = VariedadForm(instance=variedad)
    return render(request, 'variedades/formulario.html', {'form': form, 'variedad': variedad})

def eliminar_variedad(request, variedad_id):
    variedad = get_object_or_404(Variedad, pk=variedad_id)
    if request.method == 'POST':
        variedad.delete()
        messages.success(request, 'Variedad eliminada correctamente.')
        return redirect('lista_variedades')
    return render(request, 'variedades/confirmar_borrado.html', {'variedad': variedad})

def lista_parcelas(request):
    parcelas = Parcela.objects.all()
    return render(request, 'parcelas/lista.html', {'parcelas': parcelas})

def detalle_parcela(request, parcela_id):
    import string

    parcela = get_object_or_404(Parcela, pk=parcela_id)

    anio_consulta = int(request.GET.get('anio', timezone.localdate().year))

    plantaciones_activas = Plantacion.objects.filter(
        parcela=parcela
    ).filter(
        Q(fecha_siembra__year=anio_consulta) |
        Q(fecha_trasplante__year=anio_consulta) |
        Q(fecha_recoleccion_esperada__year=anio_consulta)
    ).select_related('cultivo', 'parcela', 'variedad').prefetch_related('tareas')

    hoy = timezone.localdate()
    for plantacion in plantaciones_activas:
        if plantacion.fecha_siembra:
            dias_desde_siembra = (hoy - plantacion.fecha_siembra).days
        elif plantacion.fecha_trasplante:
            dias_desde_siembra = (hoy - plantacion.fecha_trasplante).days
        else:
            dias_desde_siembra = 0

        if dias_desde_siembra < 0:
            plantacion.color_riego = '#0000ff'
        elif dias_desde_siembra <= 6:
            plantacion.color_riego = '#0000ff'
        elif dias_desde_siembra <= 10:
            plantacion.color_riego = '#ffff00'
        else:
            plantacion.color_riego = '#ff0000'

    cabecera_cols = [string.ascii_uppercase[i] for i in range(parcela.columnas)]
    grid = []

    for fila in range(1, parcela.filas + 1):
        fila_datos = []
        for columna in range(parcela.columnas):
            existe = True

            if parcela.tipo_tabla == 2:  # Triangular
                ancho_fila = 6 + (fila - 1) * (6 / 11)
                existe = columna < ancho_fila
            elif parcela.tipo_tabla == 3:  # Diagonal
                altura_minima = 6 - (columna * (6 / 9))
                existe = fila >= altura_minima

            if existe:
                plantas_en_celda = [
                    p for p in plantaciones_activas
                    if p.fila_inicio <= fila <= p.fila_fin
                    and p.columna_inicio <= columna <= p.columna_fin
                ]
                fila_datos.append({
                    'existe': True,
                    'plantas': plantas_en_celda,
                })
            else:
                fila_datos.append({
                    'existe': False,
                    'plantas': [],
                })

        grid.append(fila_datos)

    p_data = {
        'info': parcela,
        'cabecera_cols': cabecera_cols,
        'grid': grid,
    }

    familia_colors = {
        'solanaceas': '#FF6B6B',
        'leguminosas': '#4ECDC4',
        'cruciferas': '#95E1D3',
        'cucurbitaceas': '#FFE66D',
        'aliaceas': '#A8E6CF',
        'hoja': '#87CEEB',
        'gramineas': '#DEB887',
        'otros': '#D3D3D3',
    }

    familia_labels = {
        'solanaceas': 'Solanáceas (Tomate, Pimiento, Patata)',
        'leguminosas': 'Leguminosas (Haba, Guisante, Alubia)',
        'cruciferas': 'Crucíferas (Brócoli, Repollo, Coliflor)',
        'cucurbitaceas': 'Cucurbitáceas (Calabaza, Calabacín, Melón)',
        'aliaceas': 'Alíaceas (Ajo, Cebolla, Puerro)',
        'hoja': 'Hoja (Lechuga, Acelga)',
        'gramineas': 'Gramíneas (Maíz)',
        'otros': 'Otros',
    }

    leyenda = []
    familias_vistas = set()
    cultivos_familias = Cultivo.objects.values_list('familia', flat=True).distinct()
    for familia in cultivos_familias:
        if familia not in familias_vistas:
            familias_vistas.add(familia)
            leyenda.append({
                'color': familia_colors.get(familia, '#D3D3D3'),
                'label': familia_labels.get(familia, familia),
            })

    return render(request, 'parcelas/detalle.html', {
        'parcela': parcela,
        'p_data': p_data,
        'plantaciones': plantaciones_activas,
        'anio_consulta': anio_consulta,
        'leyenda': leyenda,
    })

def editar_parcela(request, parcela_id=None):
    if parcela_id:
        parcela = get_object_or_404(Parcela, pk=parcela_id)
    else:
        parcela = None
    if request.method == 'POST':
        form = ParcelaForm(request.POST, instance=parcela)
        if form.is_valid():
            form.save()
            messages.success(request, 'Parcela guardada correctamente.')
            return redirect('lista_parcelas')
    else:
        form = ParcelaForm(instance=parcela)
    return render(request, 'parcelas/formulario.html', {'form': form, 'parcela': parcela})

def eliminar_parcela(request, parcela_id):
    parcela = get_object_or_404(Parcela, pk=parcela_id)
    if request.method == 'POST':
        parcela.delete()
        messages.success(request, 'Parcela eliminada correctamente.')
        return redirect('lista_parcelas')
    return render(request, 'parcelas/confirmar_borrado.html', {'parcela': parcela})

def lista_plantaciones(request):
    # 1. Leer filtro de estado desde la querystring (?estado=...)
    estado_param = request.GET.get('estado', 'todas')
    vista_param = request.GET.get('vista', 'tarjetas')
    
    # 2. Base queryset con relaciones optimizadas
    plantaciones_qs = (
        Plantacion.objects
        .select_related('cultivo', 'parcela', 'variedad')
        .all()
    )

    # 3. Aplicar filtro por estado según tus ESTADO_CHOICES
    ESTADOS_MAP = {
        'planificada': 'planificada',
        'sembrada': 'sembrada',
        'germinada': 'germinada',
        'trasplantada': 'trasplantada',
        'en_cultivo': 'en_cultivo',
        'en_cosecha': 'en_cosecha',
        'finalizada': 'finalizada',
        'perdida': 'perdida',
    }

    if estado_param in ESTADOS_MAP:
        plantaciones_qs = plantaciones_qs.filter(estado=ESTADOS_MAP[estado_param])

    # 4. Orden lógico: por parcela, fecha de plantación (propiedad) aproximada y cultivo
    plantaciones_qs = plantaciones_qs.order_by('parcela__nombre', 'fecha_siembra', 'cultivo__nombre')

    # 5. Agrupar por parcela para la vista de tarjetas
    parcelas_dict = OrderedDict()

    for plantacion in plantaciones_qs:
        if plantacion.parcela:
            clave_parcela = plantacion.parcela.id
            nombre_parcela = plantacion.parcela.nombre
        else:
            clave_parcela = 'sin_parcela'
            nombre_parcela = 'Sin parcela'

        if clave_parcela not in parcelas_dict:
            parcelas_dict[clave_parcela] = {
                'parcela': plantacion.parcela,
                'nombre': nombre_parcela,
                'plantaciones': [],
            }

        parcelas_dict[clave_parcela]['plantaciones'].append(plantacion)

    parcelas_agrupadas = list(parcelas_dict.values())

    # 6. Métricas superiores (sobre todas las plantaciones, sin filtro por estado)
    todas = Plantacion.objects.all()

    total_plantaciones = todas.count()
    planificadas = todas.filter(estado='planificada').count()
    sembradas = todas.filter(estado='sembrada').count()
    en_cultivo = todas.filter(estado='en_cultivo').count()
    en_cosecha = todas.filter(estado='en_cosecha').count()
    finalizadas = todas.filter(estado='finalizada').count()
    perdidas = todas.filter(estado='perdida').count()

    # Métricas que puedes mostrar arriba
    activas = todas.exclude(estado__in=['finalizada', 'perdida']).count()
    cosecha_proxima = todas.filter(estado='en_cosecha').count()

    parcelas_activas = (
        todas.exclude(parcela__isnull=True)
        .values('parcela')
        .distinct()
        .count()
    )

    context = {
        'parcelas_agrupadas': parcelas_agrupadas,
        'total_plantaciones': total_plantaciones,
        'activas': activas,
        'cosecha_proxima': cosecha_proxima,
        'parcelas_activas': parcelas_activas,
        'en_cosecha': en_cosecha,
        'estado_actual': estado_param,
        'vista_actual': vista_param,
    }

    return render(request, 'plantaciones/lista_plantaciones.html', context)

def detalle_plantacion(request, plantacion_id):
    plantacion = get_object_or_404(
        Plantacion.objects.select_related('cultivo', 'parcela', 'variedad').prefetch_related(
            'tareas',
            'fotos_plantacion',
            'cosechas',
            'gastos',
        ),
        pk=plantacion_id
    )

    progreso = plantacion.calcular_progreso_ciclo()
    tareas = plantacion.tareas.all().order_by('-fecha')
    fotos = plantacion.fotos_plantacion.all().order_by('-fecha_foto', '-fecha_subida')
    cosechas = plantacion.cosechas.all().order_by('-fecha_cosecha')

    valor_total_cosechas = sum((c.total for c in cosechas), Decimal('0.00'))

    return render(request, 'plantaciones/detalle.html', {
        'plantacion': plantacion,
        'progreso': progreso,
        'tareas': tareas,
        'fotos': fotos,
        'cosechas': cosechas,
        'valor_total_cosechas': valor_total_cosechas,
    })

def agregar_foto_plantacion(request, plantacion_id):
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)

    if request.method == 'POST':
        form = FotoPlantacionForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.plantacion = plantacion
            foto.save()
            messages.success(request, 'Foto añadida al diario de cultivo.')
            return redirect('detalle_plantacion', plantacion_id=plantacion.id)
    else:
        form = FotoPlantacionForm()

    return render(request, 'plantaciones/agregar_foto.html', {
        'form': form,
        'plantacion': plantacion,
    })

def editar_plantacion(request, plantacion_id=None):
    if plantacion_id:
        plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    else:
        plantacion = None

    if request.method == 'POST':
        form = PlantacionForm(request.POST, instance=plantacion)

        if form.is_valid():
            plantacion_guardada = form.save()

            messages.success(request, 'Plantación guardada correctamente.')

            rotacion_warning = buscar_warning_rotacion(plantacion_guardada)
            if rotacion_warning:
                messages.warning(request, rotacion_warning)

            return redirect('lista_plantaciones')
        else:
            messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = PlantacionForm(instance=plantacion)

    return render(request, 'plantaciones/formulario.html', {
        'form': form,
        'plantacion': plantacion,
    })

def nueva_plantacion_mapa(request, parcela_id, fila, columna):
    parcela = get_object_or_404(Parcela, pk=parcela_id)
    
    if request.method == 'POST':
        form = PlantacionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Tomates registrados!')
            return redirect('lista_plantaciones')
    else:
        # Pasamos los valores iniciales directamente al constructor
        form = PlantacionForm(initial={
            'fila_inicio': fila,
            'columna_inicio': str(columna - 1), # Recuerda que tu ChoiceField usa strings
            'parcela': parcela.id,
            'procedencia': 'semilla_propia' if "corazón" in request.GET.get('variedad', '').lower() else 'otro'
        })
    
    return render(request, 'plantaciones/formulario.html', {'form': form, 'parcela': parcela})

def eliminar_plantacion(request, plantacion_id):
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    if request.method == 'POST':
        plantacion.delete()
        messages.success(request, 'Plantación eliminada correctamente.')
        return redirect('lista_plantaciones')
    return render(request, 'plantaciones/confirmar_borrado.html', {'plantacion': plantacion})

def agregar_cosecha(request, plantacion_id):
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    if request.method == 'POST':
        form = CosechaForm(request.POST)
        if form.is_valid():
            cosecha = form.save(commit=False)
            cosecha.plantacion = plantacion
            cosecha.save()
            messages.success(request, 'Cosecha agregada correctamente.')
            return redirect('detalle_plantacion', plantacion_id=plantacion_id)
    else:
        form = CosechaForm()
    return render(request, 'cosechas/formulario.html', {'form': form, 'plantacion': plantacion})



    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    if request.method == 'POST':
        # Nota: request.FILES es IMPRESCINDIBLE para las fotos
        form = FotoPlantacionForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.plantacion = plantacion
            foto.save()
            messages.success(request, 'Foto añadida al diario de cultivo.')
            return redirect('detalle_plantacion', plantacion_id=plantacion.id)
    else:
        form = FotoPlantacionForm()
    return render(request, 'plantaciones/agregar_foto.html', {'form': form, 'plantacion': plantacion})

def lista_tareas(request):
    hoy = timezone.localdate()
    manana = hoy + timedelta(days=1)
    proxima_semana = hoy + timedelta(days=7)

    estado_param = request.GET.get('estado', 'pendientes')
    tipo_param = request.GET.get('tipo', 'todos')

    tareas = (
        Tarea.objects
        .select_related('plantacion', 'plantacion__cultivo', 'plantacion__parcela')
        .prefetch_related('plantaciones', 'plantaciones__cultivo', 'plantaciones__parcela')
        .all()
    )

    if estado_param == 'pendientes':
        tareas = tareas.filter(completada=False)
    elif estado_param == 'completadas':
        tareas = tareas.filter(completada=True)
    elif estado_param == 'todas':
        pass

    tipos_validos = [
        'preparar',
        'siembra',
        'repicado',
        'trasplante',
        'riego',
        'abono',
        'tratamiento',
        'hedrar',
        'cosecha',
        'labores',
        'foto',
        'otros',
    ]

    if tipo_param in tipos_validos:
        tareas = tareas.filter(tipo=tipo_param)

    tareas = tareas.order_by('-fecha')

    # Panel de próximas tareas: incluye tanto tareas pendientes futuras
    # como tareas con fecha_proxima en el rango (aunque estén completadas)
    base_proximas = (
        Tarea.objects
        .select_related('plantacion', 'plantacion__cultivo', 'plantacion__parcela')
        .filter(
            Q(
                # Tareas pendientes con fecha futura
                completada=False,
                fecha__gte=hoy,
                fecha__lte=proxima_semana
            ) |
            Q(
                # Tareas con fecha_proxima futura (sin importar si están completadas)
                fecha_proxima__isnull=False,
                fecha_proxima__gte=hoy,
                fecha_proxima__lte=proxima_semana
            )
        )
        .distinct()
        .order_by('fecha', 'fecha_proxima')
    )

    # Hoy: tareas con fecha=hoy O fecha_proxima=hoy
    tareas_hoy = base_proximas.filter(
        Q(fecha=hoy) | Q(fecha_proxima=hoy)
    )

    # Mañana: tareas con fecha=mañana O fecha_proxima=mañana
    tareas_manana = base_proximas.filter(
        Q(fecha=manana) | Q(fecha_proxima=manana)
    )

    # Próximos 7 días: desde pasado mañana hasta fin de rango
    pasado_manana = hoy + timedelta(days=2)
    tareas_semana = base_proximas.filter(
        Q(
            fecha__gte=pasado_manana,
            fecha__lte=proxima_semana
        ) |
        Q(
            fecha_proxima__gte=pasado_manana,
            fecha_proxima__lte=proxima_semana
        )
    )

    todas = Tarea.objects.all()

    total_tareas = todas.count()
    pendientes = todas.filter(completada=False).count()
    completadas = todas.filter(completada=True).count()

    ultima_tarea = todas.order_by('-fecha').first()
    ultima_tarea_fecha = ultima_tarea.fecha if ultima_tarea else None
    total_tiempo_real_min = sum(
        tarea.tiempo_real_min or 0
        for tarea in todas
    )
    horas_totales = total_tiempo_real_min // 60
    minutos_restantes = total_tiempo_real_min % 60

    if horas_totales > 0 and minutos_restantes > 0:
        total_tiempo_real_texto = f"{horas_totales}h {minutos_restantes}min"
    elif horas_totales > 0:
        total_tiempo_real_texto = f"{horas_totales}h"
    else:
        total_tiempo_real_texto = f"{minutos_restantes}min"
    context = {
        'tareas': tareas,
        'tareas_hoy': tareas_hoy,
        'tareas_manana': tareas_manana,
        'tareas_semana': tareas_semana,
        'total_tareas': total_tareas,
        'pendientes': pendientes,
        'completadas': completadas,
        'ultima_tarea_fecha': ultima_tarea_fecha,
        'estado_actual': estado_param,
        'tipo_actual': tipo_param,
        'hoy': hoy,
        'manana': manana,
        'proxima_semana': proxima_semana,
        'total_tiempo_real_min': total_tiempo_real_min,
        'total_tiempo_real_texto': total_tiempo_real_texto,
    }

    return render(request, 'tareas/lista.html', context)

def nueva_tarea(request):
    initial = {}
    # Prerellenar desde URL (cuando se llega desde el plano)
    plantacion_id = request.GET.get('plantacion')
    zona = request.GET.get('zona')
    if zona:
        initial['zona'] = zona

    if request.method == 'POST':
        form = TareaForm(request.POST)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.save()
            # Guardar M2M manualmente después del save()
            # Si es todo_el_huerto, asignar todas las plantaciones activas
            if tarea.todo_el_huerto:
                tarea.plantaciones.set(Plantacion.objects.all())
            else:
                form.save_m2m()
            messages.success(request, 'Tarea creada correctamente.')
            return redirect('lista_tareas')
    else:
        form = TareaForm(initial=initial)
        # Preseleccionar plantación si viene en la URL
        if plantacion_id:
            try:
                plantacion = Plantacion.objects.get(pk=plantacion_id)
                form.fields['plantaciones'].initial = [plantacion.pk]
            except Plantacion.DoesNotExist:
                pass

    return render(request, 'tareas/formulario.html', {'form': form, 'tarea': None})

def editar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)

    if request.method == 'POST':
        form = TareaForm(request.POST, instance=tarea)
        if form.is_valid():
            tarea = form.save(commit=False)
            tarea.save()
            if tarea.todo_el_huerto:
                tarea.plantaciones.set(Plantacion.objects.all())
            else:
                form.save_m2m()
            messages.success(request, 'Tarea guardada correctamente.')
            return redirect('lista_tareas')
    else:
        form = TareaForm(instance=tarea)

    return render(request, 'tareas/formulario.html', {'form': form, 'tarea': tarea})

def eliminar_tarea(request, tarea_id):
    tarea = get_object_or_404(Tarea, pk=tarea_id)
    if request.method == 'POST':
        tarea.delete()
        messages.success(request, 'Tarea eliminada correctamente.')
        return redirect('lista_tareas')
    return render(request, 'tareas/confirmar_borrado.html', {'tarea': tarea})

def detalle_tarea(request, tarea_id):
    tarea = get_object_or_404(
        Tarea.objects.select_related(
            'plantacion',
            'plantacion__cultivo',
            'plantacion__parcela'
        ).prefetch_related(
            'plantaciones',
            'plantaciones__cultivo',
            'plantaciones__parcela'
        ),
        id=tarea_id
    )

    historial_plantacion = []

    if tarea.plantacion:
        historial_plantacion = (
            Tarea.objects
            .filter(plantacion=tarea.plantacion)
            .select_related('plantacion', 'plantacion__cultivo', 'plantacion__parcela')
            .order_by('-fecha')
        )

    context = {
        'tarea': tarea,
        'historial_plantacion': historial_plantacion,
    }
    return render(request, 'tareas/detalle.html', context)

def lista_botica(request):
    q = request.GET.get('q', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    solo_activos = request.GET.get('activos', '1')

    remedios = RemedioBotica.objects.all()

    if q:
        remedios = remedios.filter(
            Q(nombre__icontains=q) |
            Q(objetivo__icontains=q) |
            Q(ingredientes__icontains=q) |
            Q(preparacion__icontains=q)
        )

    if tipo:
        remedios = remedios.filter(tipo=tipo)

    if solo_activos == '1':
        remedios = remedios.filter(activo=True)

    context = {
        'remedios': remedios,
        'q': q,
        'tipo_actual': tipo,
        'solo_activos': solo_activos,
        'tipos': RemedioBotica.TipoRemedio.choices,
    }
    return render(request, 'botica/lista_botica.html', context)

def crear_remedio_botica(request):
    if request.method == 'POST':
        form = RemedioBoticaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Remedio guardado correctamente.')
            return redirect('lista_botica')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = RemedioBoticaForm()

    return render(request, 'botica/formulario_botica.html', {
        'form': form,
        'titulo': 'Nuevo remedio',
    })

def editar_remedio_botica(request, pk):
    remedio = get_object_or_404(RemedioBotica, pk=pk)

    if request.method == 'POST':
        form = RemedioBoticaForm(request.POST, instance=remedio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Remedio actualizado correctamente.')
            return redirect('lista_botica')
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = RemedioBoticaForm(instance=remedio)

    return render(request, 'botica/formulario_botica.html', {
        'form': form,
        'titulo': f'Editar: {remedio.nombre}',
        'remedio': remedio,
    })

def detalle_remedio_botica(request, pk):
    remedio = get_object_or_404(RemedioBotica, pk=pk)
    aplicaciones = remedio.aplicaciones.all()

    return render(request, 'botica/detalle_botica.html', {
        'remedio': remedio,
        'aplicaciones': aplicaciones,
    })

def crear_aplicacion_remedio(request, remedio_pk):
    remedio = get_object_or_404(RemedioBotica, pk=remedio_pk)

    if request.method == 'POST':
        form = AplicacionRemedioForm(request.POST, remedio=remedio)
        if form.is_valid():
            aplicacion = form.save(commit=False)
            aplicacion.remedio = remedio
            aplicacion.save()

            crear_seguimiento = form.cleaned_data.get('crear_seguimiento')
            dias_hasta_seguimiento = form.cleaned_data.get('dias_hasta_seguimiento') or 7

            if crear_seguimiento:
                fecha_seguimiento = timezone.localdate() + timedelta(days=dias_hasta_seguimiento)

                # Buscar la plantación asociada al cultivo de la aplicación
                plantacion_obj = None
                if aplicacion.cultivo and aplicacion.parcela:
                    # Si hay cultivo y parcela, buscar la plantación activa que los vincule
                    plantacion_obj = Plantacion.objects.filter(
                        cultivo=aplicacion.cultivo,
                        parcela=aplicacion.parcela
                    ).first()

                tarea = Tarea.objects.create(
                    tipo='tratamiento',
                    descripcion=(
                        f"🔍 Revisar efecto del remedio '{remedio.nombre}' "
                        f"aplicado contra: {aplicacion.problema_detectado}.\n\n"
                        f"Dosis aplicada: {aplicacion.dosis_aplicada or 'No especificada'}.\n"
                        f"Condiciones: {aplicacion.condiciones or 'No especificadas'}.\n"
                        f"Observar si el problema mejoró, empeoró o se mantiene igual."
                    ),
                    fecha=fecha_seguimiento,
                    completada=False,
                    plantacion=plantacion_obj,
                    todo_el_huerto=False,
                )

                # Si más adelante añades el campo tarea_seguimiento en AplicacionRemedio,
                # descomenta estas dos líneas:
                aplicacion.tarea_seguimiento = tarea
                aplicacion.save(update_fields=['tarea_seguimiento'])

                messages.success(
                    request,
                    f'✅ Aplicación registrada correctamente. Se ha creado una tarea de seguimiento para el {fecha_seguimiento.strftime("%d/%m/%Y")}.'
                )
            else:
                messages.success(request, '✅ Aplicación registrada correctamente.')

            return redirect('detalle_remedio_botica', pk=remedio.pk)

        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = AplicacionRemedioForm(remedio=remedio)

    return render(request, 'botica/formulario_aplicacion_remedio.html', {
        'form': form,
        'remedio': remedio,
        'titulo': f'Registrar aplicación: {remedio.nombre}',
    })

def editar_aplicacion_remedio(request, pk):
    aplicacion = get_object_or_404(AplicacionRemedio, pk=pk)

    if request.method == 'POST':
        form = AplicacionRemedioForm(request.POST, instance=aplicacion, remedio=aplicacion.remedio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aplicación actualizada correctamente.')
            return redirect('detalle_remedio_botica', pk=aplicacion.remedio.pk)
        messages.error(request, 'Revisa los errores del formulario.')
    else:
        form = AplicacionRemedioForm(instance=aplicacion, remedio=aplicacion.remedio)

    return render(request, 'botica/formulario_aplicacion_remedio.html', {
        'form': form,
        'remedio': aplicacion.remedio,
        'aplicacion': aplicacion,
        'titulo': f'Editar aplicación: {aplicacion.remedio.nombre}',
    })

def lista_gastos(request):
    gastos = Gasto.objects.all()

    categoria_filtro = request.GET.get('categoria')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if categoria_filtro:
        gastos = gastos.filter(categoria=categoria_filtro)
    if fecha_desde:
        gastos = gastos.filter(fecha_compra__gte=fecha_desde)
    if fecha_hasta:
        gastos = gastos.filter(fecha_compra__lte=fecha_hasta)

    gasto_total = sum(g.coste_total for g in gastos)
    gasto_promedio = gasto_total / gastos.count() if gastos.exists() else Decimal('0.00')

    cosechas = Cosecha.objects.all()
    ahorro_total = sum(c.total for c in cosechas)

    balance_neto = ahorro_total - gasto_total

    stats_por_categoria = {}
    for gasto in gastos:
        cat_label = gasto.get_categoria_display()
        if cat_label not in stats_por_categoria:
            stats_por_categoria[cat_label] = {
                'total': Decimal('0.00'),
                'cantidad': 0
            }
        stats_por_categoria[cat_label]['total'] += gasto.coste_total
        stats_por_categoria[cat_label]['cantidad'] += 1

    return render(request, 'gastos/lista.html', {
        'gastos': gastos,
        'gasto_total': gasto_total,
        'gasto_promedio': gasto_promedio,
        'ahorro_total': ahorro_total,
        'balance_neto': balance_neto,
        'categorias': Gasto.CATEGORIA_CHOICES,
        'stats_por_categoria': stats_por_categoria,
    })

def editar_gasto(request, gasto_id=None):
    if gasto_id:
        gasto = get_object_or_404(Gasto, pk=gasto_id)
        accion = 'Editar'
    else:
        gasto = None
        accion = 'Nuevo'

    if request.method == 'POST':
        form = GastoForm(request.POST, request.FILES, instance=gasto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gasto guardado correctamente.')
            return redirect('lista_gastos')
    else:
        form = GastoForm(instance=gasto)

    return render(request, 'gastos/formulario.html', {
        'form': form,
        'gasto': gasto,
        'accion': accion,
    })

def eliminar_gasto(request, gasto_id):
    gasto = get_object_or_404(Gasto, pk=gasto_id)

    if request.method == 'POST':
        gasto.delete()
        messages.success(request, 'Gasto eliminado correctamente.')
        return redirect('lista_gastos')

    return render(request, 'gastos/confirmar_borrado.html', {
        'gasto': gasto,
    })

def galeria_general(request):
    etiqueta_filtro = request.GET.get('etiqueta', '')
    fotos = FotoHuerto.objects.all()
    if etiqueta_filtro:
        fotos = fotos.filter(etiqueta=etiqueta_filtro)
    return render(request, 'galeria/galeria_general.html', {
        'fotos': fotos,
        'etiqueta_filtro': etiqueta_filtro,
    })

def subir_foto_seleccionar(request):
    plantaciones = Plantacion.objects.select_related('cultivo', 'parcela').all()
    return render(request, 'galeria/subir_foto_seleccionar.html', {'plantaciones': plantaciones})

def galeria_plantacion(request, plantacion_id):
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    etiqueta_filtro = request.GET.get('etiqueta', '')
    fotos = plantacion.fotos.all()
    if etiqueta_filtro:
        fotos = fotos.filter(etiqueta=etiqueta_filtro)
    if request.GET.get('solo_hitos'):
        fotos = fotos.filter(es_hito=True)
    return render(request, 'galeria/galeria_plantacion.html', {
        'plantacion': plantacion,
        'fotos': fotos,
        'etiquetas': FOTO_ETIQUETA_CHOICES,
        'etiqueta_filtro': etiqueta_filtro,
    })

def subir_foto(request, plantacion_id=None):
    if plantacion_id is None:
        return redirect('subir_foto_seleccionar')

    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)

    if request.method == 'POST':
        form = FotoHuertoForm(request.POST, request.FILES)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.plantacion = plantacion
            foto.save()
            messages.success(request, 'Foto subida correctamente.')
            return redirect('galeria_plantacion', plantacion_id=plantacion.id)
    else:
        form = FotoHuertoForm()
    return render(request, 'galeria/formulario_foto.html', {
        'form': form,
        'plantacion': plantacion,
        'titulo': 'Subir Foto',
        'es_edicion': False,
    })

def editar_foto(request, foto_id):
    foto = get_object_or_404(FotoHuerto, pk=foto_id)
    if request.method == 'POST':
        form = FotoHuertoForm(request.POST, request.FILES, instance=foto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Foto editada correctamente.')
            return redirect('galeria_general')
    else:
        form = FotoHuertoForm(instance=foto)
    return render(request, 'galeria/formulario_foto.html', {
        'form': form,
        'foto': foto,
        'plantacion': foto.plantacion,
        'titulo': 'Editar Foto',
        'es_edicion': True,
    })

def eliminar_foto(request, foto_id):
    foto = get_object_or_404(FotoHuerto, pk=foto_id)
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Foto eliminada correctamente.')
        return redirect('galeria_general')
    return render(request, 'galeria/confirmar_borrado_foto.html', {'foto': foto})

def detalle_foto(request, foto_id):
    foto = get_object_or_404(FotoHuerto, pk=foto_id)
    return render(request, 'galeria/detalle_foto.html', {'foto': foto})




def lista_cosechas(request):
    cosechas = Cosecha.objects.select_related('plantacion', 'plantacion__cultivo').order_by('-fecha_cosecha', '-id')
    return render(request, 'cosechas/lista.html', {
        'cosechas': cosechas
    })


def agregar_cosecha(request, plantacion_id):
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)

    if request.method == 'POST':
        form = CosechaForm(request.POST)
        if form.is_valid():
            cosecha = form.save(commit=False)
            cosecha.plantacion = plantacion
            cosecha.save()
            messages.success(request, 'Cosecha registrada correctamente.')
            return redirect('detalle_plantacion', plantacion_id=plantacion.id)
    else:
        form = CosechaForm()

    return render(request, 'cosechas/formulario.html', {
        'form': form,
        'cosecha': None,
        'plantacion': plantacion,
        'accion': 'Registrar',
    })


def editar_cosecha(request, cosecha_id):
    cosecha = get_object_or_404(
        Cosecha.objects.select_related('plantacion', 'plantacion__cultivo'),
        pk=cosecha_id
    )
    plantacion = cosecha.plantacion

    if request.method == 'POST':
        form = CosechaForm(request.POST, instance=cosecha)
        if form.is_valid():
            cosecha_editada = form.save(commit=False)
            cosecha_editada.plantacion = plantacion
            cosecha_editada.save()
            messages.success(request, 'Cosecha actualizada correctamente.')
            return redirect('detalle_plantacion', plantacion_id=plantacion.id)
    else:
        form = CosechaForm(instance=cosecha)

    return render(request, 'cosechas/formulario.html', {
        'form': form,
        'cosecha': cosecha,
        'plantacion': plantacion,
        'accion': 'Editar',
    })


def eliminar_cosecha(request, cosecha_id):
    cosecha = get_object_or_404(
        Cosecha.objects.select_related('plantacion', 'plantacion__cultivo'),
        pk=cosecha_id
    )
    plantacion = cosecha.plantacion

    if request.method == 'POST':
        cosecha.delete()
        messages.success(request, 'Cosecha eliminada correctamente.')
        return redirect('detalle_plantacion', plantacion_id=plantacion.id)

    return render(request, 'cosechas/confirmar_borrado.html', {
        'cosecha': cosecha,
        'plantacion': plantacion,
    })

def analisis_economico(request):
    # Análisis económico
    return render(request, 'analisis_economico.html')

def calendario(request):
    # Calendario
    return render(request, 'calendario/lista.html')


def plano_huerto(request):
    """
    Genera el mapa de cultivos del huerto con grid visual de plantaciones.
    
    Mejoras aplicadas:
    - Plantaciones activas correctamente filtradas por ciclo de vida
    - Estado de riego basado en última tarea real de riego
    - Rendimiento optimizado con prefetch y agrupación
    - Compatibilidad con campos deprecados
    """
    from datetime import timedelta
    from collections import defaultdict
    import string
    
    # Año seleccionado (por defecto el actual)
    anio_consulta = int(request.GET.get('anio', timezone.localdate().year))
    
    # Lista de años disponibles
    plantaciones_all = Plantacion.objects.exclude(
        fecha_siembra__isnull=True
    ).values_list('fecha_siembra__year', flat=True).distinct()
    
    plantaciones_trasplante = Plantacion.objects.exclude(
        fecha_trasplante__isnull=True
    ).values_list('fecha_trasplante__year', flat=True).distinct()
    
    anos_set = set(plantaciones_all) | set(plantaciones_trasplante)
    lista_anios = sorted(anos_set) if anos_set else [timezone.localdate().year]
    
    # Fechas límite del año consultado
    inicio_anio = timezone.datetime(anio_consulta, 1, 1).date()
    fin_anio = timezone.datetime(anio_consulta, 12, 31).date()
    
    # Obtener plantaciones que ESTÁN VIVAS durante el año consultado
    # Una plantación está viva si:
    # - Tiene fecha de inicio (siembra o trasplante) antes del fin del año
    # - Y no ha terminado antes del inicio del año (o no tiene fecha de fin)
    plantaciones_activas = Plantacion.objects.filter(
        Q(
            # Plantaciones que empiezan durante o antes del año consultado
            Q(fecha_siembra__lte=fin_anio) | Q(fecha_trasplante__lte=fin_anio)
        ),
        Q(
            # Y que no han terminado antes del inicio del año
            Q(fecha_recoleccion_inicio__isnull=True) |
            Q(fecha_recoleccion_inicio__gte=inicio_anio) |
            Q(fecha_recoleccion_esperada__isnull=True) |
            Q(fecha_recoleccion_esperada__gte=inicio_anio)
        )
    ).select_related(
        'cultivo', 'parcela', 'variedad'
    ).prefetch_related(
        'tareas'
    ).distinct()
    
    # Calcular estado de riego basado en la última tarea de riego real
    hoy = timezone.localdate()
    
    for plantacion in plantaciones_activas:
        # Buscar la última tarea de riego completada para esta plantación
        ultima_tarea_riego = plantacion.tareas.filter(
            tipo='riego',
            completada=True
        ).order_by('-fecha').first()
        
        if ultima_tarea_riego:
            dias_desde_riego = (hoy - ultima_tarea_riego.fecha).days
        else:
            # Si no hay riegos registrados, usar la fecha de inicio como fallback
            fecha_inicio = plantacion.fecha_trasplante or plantacion.fecha_siembra
            if fecha_inicio:
                dias_desde_riego = (hoy - fecha_inicio).days
            else:
                dias_desde_riego = 999  # Valor alto para marcar como urgente
        
        # Asignar color según días desde último riego
        if dias_desde_riego < 0:
            plantacion.color_riego = '#0000ff'  # Futuro (no debería pasar)
        elif dias_desde_riego <= 3:
            plantacion.color_riego = '#0000ff'  # Azul: óptimo (riego reciente)
        elif dias_desde_riego <= 6:
            plantacion.color_riego = '#ffff00'  # Amarillo: atención
        else:
            plantacion.color_riego = '#ff0000'  # Rojo: urgente
        
        plantacion.dias_desde_riego = dias_desde_riego
    
    # Agrupar plantaciones por parcela para optimizar el bucle
    plantaciones_por_parcela = defaultdict(list)
    for p in plantaciones_activas:
        plantaciones_por_parcela[p.parcela_id].append(p)
    
    # Generar datos de parcelas
    parcelas = Parcela.objects.all().order_by('nombre')
    parcelas_data = []
    
    for parcela in parcelas:
        # Generar columnas (A, B, C, ...)
        cabecera_cols = [string.ascii_uppercase[i] for i in range(parcela.columnas)]
        
        # Obtener solo las plantaciones de esta parcela
        plantaciones_parcela = plantaciones_por_parcela.get(parcela.id, [])
        
        # Generar grid
        grid = []
        for fila in range(1, parcela.filas + 1):
            fila_datos = []
            for columna in range(parcela.columnas):
                # Verificar si la celda existe según tipo de tabla
                existe = True
                if parcela.tipo_tabla == 2:  # Triangular
                    ancho_fila = 6 + (fila - 1) * (6 / 11)
                    existe = columna < ancho_fila
                elif parcela.tipo_tabla == 3:  # Diagonal
                    altura_minima = 6 - (columna * (6 / 9))
                    existe = fila >= altura_minima
                
                if existe:
                    # Buscar plantaciones solo en las de esta parcela
                    plantas_en_celda = [
                        p for p in plantaciones_parcela
                        if (p.fila_inicio <= fila <= p.fila_fin and
                            p.columna_inicio <= columna <= p.columna_fin)
                    ]
                    fila_datos.append({
                        'existe': True,
                        'plantas': plantas_en_celda,
                    })
                else:
                    fila_datos.append({
                        'existe': False,
                        'plantas': [],
                    })
            
            grid.append(fila_datos)
        
        parcelas_data.append({
            'info': parcela,
            'cabecera_cols': cabecera_cols,
            'grid': grid,
        })
    
    # Generar leyenda de familias
    familia_colors = {
        'solanaceas': '#FF6B6B',
        'leguminosas': '#4ECDC4',
        'cruciferas': '#95E1D3',
        'cucurbitaceas': '#FFE66D',
        'aliaceas': '#A8E6CF',
        'hoja': '#87CEEB',
        'gramineas': '#DEB887',
        'umbeliferas': '#FFB347',
        'compuestas': '#B19CD9',
        'otros': '#D3D3D3',
    }
    
    familia_labels = {
        'solanaceas': 'Solanáceas (Tomate, Pimiento, Patata)',
        'leguminosas': 'Leguminosas (Haba, Guisante, Alubia)',
        'cruciferas': 'Crucíferas (Brócoli, Repollo, Coliflor)',
        'cucurbitaceas': 'Cucurbitáceas (Calabaza, Calabacín, Melón)',
        'aliaceas': 'Alíaceas (Ajo, Cebolla, Puerro)',
        'hoja': 'Hoja (Lechuga, Acelga)',
        'gramineas': 'Gramíneas (Maíz)',
        'umbeliferas': 'Umbelíferas (Zanahoria, Apio)',
        'compuestas': 'Compuestas (Alcachofa, Girasol)',
        'otros': 'Otros',
    }
    
    leyenda = []
    familias_vistas = set()
    cultivos_familias = Cultivo.objects.values_list('familia', flat=True).distinct()
    for familia in cultivos_familias:
        if familia not in familias_vistas:
            familias_vistas.add(familia)
            leyenda.append({
                'color': familia_colors.get(familia, '#D3D3D3'),
                'label': familia_labels.get(familia, familia.capitalize()),
            })
    
    # Alertas de cosecha próxima (próximos 7 días)
    proxima_semana = hoy + timedelta(days=7)
    
    # Usar la propiedad fecha_cosecha_estimada o buscar en ambos campos
    alertas_cosecha = []
    for p in plantaciones_activas:
        fecha_cosecha = p.fecha_cosecha_estimada  # Usa la propiedad que ya maneja compatibilidad
        if fecha_cosecha and hoy <= fecha_cosecha <= proxima_semana:
            alertas_cosecha.append(p)
    
    context = {
        'parcelas_data': parcelas_data,
        'leyenda': leyenda,
        'lista_anios': lista_anios,
        'anio_consulta': anio_consulta,
        'alertas_cosecha': alertas_cosecha,
    }
    
    return render(request, 'plano.html', context)

class RotacionResumenListView(ListView):
    model = Parcela
    template_name = 'huerto/rotaciones/resumen.html'
    context_object_name = 'parcelas'

    def get_queryset(self):
        return Parcela.objects.prefetch_related('rotaciones__cultivo').all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        mapa_grupos = {
            'fruto': 'Grupo A — Fruto',
            'hoja_raiz': 'Grupo B — Hoja/Raíz',
            'leguminosa': 'Grupo C — Leguminosa',
            'bulbo': 'Grupo D — Bulbo/Limpieza',
        }

        resumen = []

        for parcela in context['parcelas']:
            ultima = parcela.ultima_rotacion()
            siguiente = parcela.siguiente_grupo_recomendado()

            resumen.append({
                'parcela': parcela,
                'ultima_rotacion': ultima,
                'familias_recientes': parcela.familias_ultimos_anos(4),
                'grupos_recientes': parcela.grupos_ultimos_anos(4),
                'siguiente_grupo_codigo': siguiente,
                'siguiente_grupo_label': mapa_grupos.get(siguiente, 'Sin definir'),
            })

        context['resumen_rotaciones'] = resumen
        return context


class RotacionParcelaCreateView(CreateView):
    model = RotacionParcela
    form_class = RotacionParcelaForm
    template_name = 'huerto/rotaciones/formulario.html'
    success_url = reverse_lazy('rotaciones_resumen')

    def form_valid(self, form):
        messages.success(self.request, 'Rotación guardada correctamente.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Revisa los datos del formulario.')
        return super().form_invalid(form)


#Rotaciones
def plan_rotaciones(request):
    """
    Pantalla general con reglas y recomendaciones de rotación.
    """

    familias_rotacion = [
        {
            'nombre': 'Solanáceas',
            'ejemplos': 'Tomate, pimiento, berenjena, patata',
            'evitar': 'No repetir en la misma parcela durante varios años',
        },
        {
            'nombre': 'Cucurbitáceas',
            'ejemplos': 'Calabacín, pepino, melón, calabaza',
            'evitar': 'Evitar repetir tras otra cucurbitácea',
        },
        {
            'nombre': 'Crucíferas',
            'ejemplos': 'Col, brócoli, coliflor, rábano',
            'evitar': 'Vigilar repetición por plagas y agotamiento',
        },
        {
            'nombre': 'Hoja',
            'ejemplos': 'Lechuga, espinaca, acelga',
            'evitar': 'No abusar sin mejora previa del suelo',
        },
        {
            'nombre': 'Umbelíferas',
            'ejemplos': 'Zanahoria, apio, perejil, hinojo',
            'evitar': 'No repetir continuamente en la misma zona',
        },
        {
            'nombre': 'Leguminosas',
            'ejemplos': 'Haba, guisante, judía',
            'evitar': 'No hacer monocultivo continuado',
        },
        {
            'nombre': 'Alíaceas',
            'ejemplos': 'Ajo, cebolla, puerro',
            'evitar': 'No repetir aliáceas justo después de aliáceas',
        },
        {
            'nombre': 'Compuestas',
            'ejemplos': 'Lechuga, alcachofa, girasol',
            'evitar': 'Separar bien de cultivos muy exigentes si el suelo está pobre',
        },
    ]

    recomendaciones = [
        {
            'grupo_actual': 'Leguminosa',
            'aporte': 'Mejora fertilidad y aporta nitrógeno',
            'siguiente': 'Hoja / Fruto',
            'evitar': 'Otra leguminosa seguida',
        },
        {
            'grupo_actual': 'Hoja / Raíz',
            'aporte': 'Consumo medio de nutrientes',
            'siguiente': 'Fruto / Bulbo',
            'evitar': 'Misma familia repetida',
        },
        {
            'grupo_actual': 'Fruto',
            'aporte': 'Muy exigente en nutrientes',
            'siguiente': 'Leguminosa / Bulbo',
            'evitar': 'Más fruto seguido',
        },
        {
            'grupo_actual': 'Bulbo',
            'aporte': 'Menor exigencia y buen cierre de ciclo',
            'siguiente': 'Leguminosa / Hoja',
            'evitar': 'Otra aliácea seguida',
        },
    ]

    observaciones_ecologicas = [
        'No repetir la misma familia botánica en la misma parcela.',
        'Intentar dejar 3-4 campañas antes de repetir familias sensibles.',
        'Las leguminosas son buenas predecesoras de cultivos exigentes.',
        'Las solanáceas y crucíferas necesitan más vigilancia sanitaria.',
    ]

    context = {
        'familias_rotacion': familias_rotacion,
        'recomendaciones': recomendaciones,
        'observaciones_ecologicas': observaciones_ecologicas,
    }

    return render(request, 'rotaciones/plan_rotaciones.html', context)


def rotaciones_parcelas(request):
    """
    Pantalla con resumen de rotación por parcela:
    cultivo predominante, cultivo anterior y siguiente recomendado.
    """

    parcelas = Parcela.objects.all().prefetch_related(
        'plantaciones__cultivo',
        'historial_rotaciones__cultivo_anterior',
        'historial_rotaciones__cultivo_siguiente',
    ).order_by('nombre')

    parcelas_resumen = []
    parcelas_con_aviso = 0
    parcelas_leguminosa = 0

    mapa_grupos = {
        'fruto': 'Fruto',
        'hoja_raiz': 'Hoja / Raíz',
        'leguminosa': 'Leguminosa',
        'bulbo': 'Bulbo / Limpieza',
    }

    sugerencias_por_grupo = {
        'fruto': 'Tomate, pimiento, calabacín',
        'hoja_raiz': 'Lechuga, acelga, zanahoria, col',
        'leguminosa': 'Haba, guisante, judía',
        'bulbo': 'Ajo, cebolla, puerro',
    }

    secuencia = ['leguminosa', 'hoja_raiz', 'fruto', 'bulbo']

    for parcela in parcelas:
        plantaciones = list(parcela.plantaciones.all())

        contador_cultivos = Counter()
        contador_familias = Counter()
        familias_presentes = set()

        for plantacion in plantaciones:
            if plantacion.cultivo:
                nombre_cultivo = plantacion.cultivo.nombre
                familia = plantacion.cultivo.get_familia_display()
                grupo = plantacion.cultivo.grupo_rotacion

                peso = plantacion.cantidad if plantacion.cantidad else 1

                contador_cultivos[nombre_cultivo] += peso
                contador_familias[familia] += peso
                familias_presentes.add(familia)

        cultivo_predominante = contador_cultivos.most_common(1)[0][0] if contador_cultivos else 'Sin plantaciones'
        familia_predominante = contador_familias.most_common(1)[0][0] if contador_familias else 'Sin familia definida'

        plantacion_predominante = None
        if plantaciones and contador_cultivos:
            nombre_predominante = contador_cultivos.most_common(1)[0][0]
            for plantacion in plantaciones:
                if plantacion.cultivo and plantacion.cultivo.nombre == nombre_predominante:
                    plantacion_predominante = plantacion
                    break

        grupo_actual_codigo = None
        if plantacion_predominante and plantacion_predominante.cultivo:
            grupo_actual_codigo = plantacion_predominante.cultivo.grupo_rotacion

        historial = parcela.historial_rotaciones.all().order_by('-fecha_rotacion')
        ultima_rotacion = historial.first()

        cultivo_anterior = None
        familia_anterior = None

        if ultima_rotacion and ultima_rotacion.cultivo_anterior:
            cultivo_anterior = ultima_rotacion.cultivo_anterior.nombre
            familia_anterior = ultima_rotacion.cultivo_anterior.get_familia_display()

        if grupo_actual_codigo in secuencia:
            idx = secuencia.index(grupo_actual_codigo)
            siguiente_codigo = secuencia[(idx + 1) % len(secuencia)]
        else:
            siguiente_codigo = 'leguminosa'

        siguiente_grupo = mapa_grupos.get(siguiente_codigo, 'Leguminosa')
        sugerencias = sugerencias_por_grupo.get(siguiente_codigo, 'Haba, guisante, judía')

        estado_rotacion = 'ok'
        observacion = 'Rotación correcta.'

        if ultima_rotacion and ultima_rotacion.cultivo_siguiente and plantacion_predominante and plantacion_predominante.cultivo:
            familia_actual_codigo = plantacion_predominante.cultivo.familia
            familia_ultima_codigo = ultima_rotacion.cultivo_siguiente.familia

            if familia_actual_codigo == familia_ultima_codigo:
                estado_rotacion = 'peligro'
                observacion = 'Se repite la misma familia que en la última rotación registrada.'
                parcelas_con_aviso += 1
            elif grupo_actual_codigo == ultima_rotacion.cultivo_siguiente.grupo_rotacion:
                estado_rotacion = 'aviso'
                observacion = 'Se repite el mismo grupo de rotación; conviene revisarlo.'
                parcelas_con_aviso += 1
            else:
                observacion = 'La parcela puede seguir la rotación prevista.'
        else:
            if grupo_actual_codigo == 'fruto':
                observacion = 'Conviene pasar a leguminosa o bulbo en la siguiente campaña.'
            elif grupo_actual_codigo == 'leguminosa':
                observacion = 'Buen momento para meter hoja o fruto exigente después.'
            elif grupo_actual_codigo == 'bulbo':
                observacion = 'Parcela adecuada para volver a leguminosa o cultivos de hoja.'
            elif grupo_actual_codigo == 'hoja_raiz':
                observacion = 'Después puede entrar fruto o bulbo según fertilidad.'
            else:
                observacion = 'Falta historial para afinar la recomendación.'

        if siguiente_codigo == 'leguminosa':
            parcelas_leguminosa += 1

        parcelas_resumen.append({
            'parcela': parcela,
            'estado_rotacion': estado_rotacion,
            'cultivo_predominante': cultivo_predominante,
            'familia_predominante': familia_predominante,
            'cultivo_anterior': cultivo_anterior,
            'familia_anterior': familia_anterior,
            'siguiente_grupo': siguiente_grupo,
            'sugerencias': sugerencias,
            'observacion': observacion,
            'familias_presentes': sorted(familias_presentes),
        })

    context = {
        'total_parcelas': parcelas.count(),
        'parcelas_con_aviso': parcelas_con_aviso,
        'parcelas_leguminosa': parcelas_leguminosa,
        'parcelas_resumen': parcelas_resumen,
        'hoy': timezone.localdate(),
    }

    return render(request, 'rotaciones/parcelas_rotacion.html', context)




@require_POST
def registrar_riego_rapido(request):
    """
    Registra una tarea de riego para múltiples plantaciones desde el plano.
    Recibe un JSON con lista de IDs de plantaciones.
    """
    try:
        data = json.loads(request.body)
        plantacion_ids = data.get('plantaciones', [])
        
        if not plantacion_ids:
            return JsonResponse({
                'success': False,
                'error': 'No se seleccionaron plantaciones'
            })
        
        hoy = timezone.localdate()
        plantaciones = Plantacion.objects.filter(id__in=plantacion_ids)
        
        if not plantaciones.exists():
            return JsonResponse({
                'success': False,
                'error': 'Plantaciones no encontradas'
            })
        
        # Crear una tarea de riego por cada plantación
        tareas_creadas = []
        for plantacion in plantaciones:
            tarea = Tarea.objects.create(
                tipo='riego',
                descripcion=f'Riego registrado desde plano para {plantacion.nombre_completo}',
                fecha=hoy,
                completada=True,  # Se marca como completada porque ya se hizo
                plantacion=plantacion
            )
            tareas_creadas.append(tarea.id)
        
        return JsonResponse({
            'success': True,
            'tareas_creadas': len(tareas_creadas),
            'message': f'Riego registrado para {len(tareas_creadas)} plantación(es)'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })