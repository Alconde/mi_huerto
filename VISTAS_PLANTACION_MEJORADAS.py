# ===================================================================
# VISTAS MEJORADAS PARA PLANTACION CON CICLO DE VIDA Y FOTOS
# ===================================================================
# Este archivo contiene ejemplos de cómo actualizar tus vistas en views.py
# para manejar correctamente el ciclo de vida de plantaciones y fotos.
#
# INSTRUCCIONES:
# 1. Copia el contenido relevante a tu views.py existente
# 2. Reemplaza las vistas de edición de plantación
# 3. Agrega las nuevas vistas para fotos

from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from .models import *
from .forms import *


# ===================================================================
# VISTA MEJORADA DE EDICIÓN DE PLANTACIÓN
# ===================================================================
def editar_plantacion(request, plantacion_id=None):
    """
    Vista de edición mejorada que:
    - Usa instance=plantacion para cargar valores existentes
    - Muestra correctamente todos los campos de fecha
    - Mantiene datos al editar
    """
    if plantacion_id:
        plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    else:
        plantacion = None
    
    if request.method == 'POST':
        form = PlantacionForm(request.POST, instance=plantacion)
        if form.is_valid():
            form.save()
            if plantacion_id:
                messages.success(request, f'Plantación de {form.instance.cultivo.nombre} actualizada correctamente.')
                return redirect('detalle_plantacion', plantacion_id=plantacion_id)
            else:
                messages.success(request, 'Nueva plantación creada correctamente.')
                return redirect('lista_plantaciones')
        else:
            messages.error(request, 'Error al guardar la plantación. Revisa los campos.')
    else:
        # IMPORTANTE: Pasar instance=plantacion para cargar valores existentes
        form = PlantacionForm(instance=plantacion)
    
    context = {
        'form': form,
        'plantacion': plantacion,
        'es_nueva': plantacion is None,
    }
    return render(request, 'plantaciones/formulario.html', context)


# ===================================================================
# VISTA DE DETALLE DE PLANTACIÓN CON PROGRESO Y FOTOS
# ===================================================================
def detalle_plantacion(request, plantacion_id):
    """
    Vista detallada que muestra:
    - Información completa de la plantación
    - Progreso del ciclo con cálculos
    - Histórico de fotos
    - Cosechas registradas
    """
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    
    # Calcular progreso del ciclo
    progreso = plantacion.calcular_progreso_ciclo()
    
    # Obtener fotos del histórico (paginadas)
    fotos_page = request.GET.get('fotos_page', 1)
    fotos_paginator = Paginator(plantacion.fotos_plantacion.all(), 6)
    fotos = fotos_paginator.get_page(fotos_page)
    
    # Obtener cosechas
    cosechas = plantacion.cosechas.all()
    
    # Calcular estadísticas
    dias_desde_siembra = plantacion.dias_ciclo_actual
    
    context = {
        'plantacion': plantacion,
        'progreso': progreso,
        'dias_desde_siembra': dias_desde_siembra,
        'fotos': fotos,
        'cosechas': cosechas,
        'fecha_siembra_display': plantacion.fecha_siembra_real or plantacion.fecha_siembra_estimada or plantacion.fecha_siembra,
    }
    return render(request, 'plantaciones/detalle.html', context)


# ===================================================================
# VISTAS PARA GESTIONAR FOTOS DE PLANTACIÓN
# ===================================================================
def agregar_foto_plantacion(request, plantacion_id):
    """
    Agrega una foto al histórico de una plantación.
    La fecha se toma automáticamente como hoy.
    Los días del ciclo se calculan automáticamente.
    """
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    
    if request.method == 'POST':
        form = FotoPlantacionForm(request.POST, request.FILES, plantacion=plantacion)
        if form.is_valid():
            foto = form.save(commit=False)
            foto.plantacion = plantacion
            foto.save()
            messages.success(request, 'Foto agregada al histórico de la plantación.')
            return redirect('detalle_plantacion', plantacion_id=plantacion_id)
        else:
            messages.error(request, 'Error al guardar la foto.')
    else:
        form = FotoPlantacionForm(plantacion=plantacion)
    
    context = {
        'form': form,
        'plantacion': plantacion,
    }
    return render(request, 'plantaciones/agregar_foto.html', context)


def galeria_fotos_plantacion(request, plantacion_id):
    """
    Muestra todas las fotos de una plantación organizadas por tipo.
    """
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    
    # Agrupar fotos por tipo
    fotos_por_tipo = {}
    for tipo_label, tipo_value in FotoPlantacion.TIPO_FOTO_CHOICES:
        fotos = plantacion.fotos_plantacion.filter(tipo_foto=tipo_value)
        if fotos.exists():
            fotos_por_tipo[tipo_label] = fotos
    
    context = {
        'plantacion': plantacion,
        'fotos_por_tipo': fotos_por_tipo,
    }
    return render(request, 'plantaciones/galeria_fotos.html', context)


def eliminar_foto_plantacion(request, foto_id):
    """
    Elimina una foto del histórico.
    """
    foto = get_object_or_404(FotoPlantacion, pk=foto_id)
    plantacion_id = foto.plantacion.id
    
    if request.method == 'POST':
        foto.delete()
        messages.success(request, 'Foto eliminada del histórico.')
        return redirect('detalle_plantacion', plantacion_id=plantacion_id)
    
    context = {
        'foto': foto,
        'plantacion': foto.plantacion,
    }
    return render(request, 'plantaciones/confirmar_eliminar_foto.html', context)


# ===================================================================
# VISTA DE RESUMEN CON PROGRESO DE TODAS LAS PLANTACIONES
# ===================================================================
def lista_plantaciones_con_progreso(request):
    """
    Lista todas las plantaciones activas con su progreso actual.
    Filtra plantaciones no cosechadas por defecto.
    """
    plantaciones = Plantacion.objects.filter(
        cosechas__isnull=True  # No cosechadas
    ).distinct().order_by('-fecha_siembra_real', '-fecha_siembra')
    
    # Filtrar por cultivo si se especifica
    cultivo_id = request.GET.get('cultivo')
    if cultivo_id:
        plantaciones = plantaciones.filter(cultivo_id=cultivo_id)
    
    # Calcular progreso para cada plantación
    plantaciones_con_progreso = []
    for plantacion in plantaciones:
        progreso = plantacion.calcular_progreso_ciclo()
        plantaciones_con_progreso.append({
            'plantacion': plantacion,
            'progreso': progreso,
        })
    
    cultivos = Cultivo.objects.all()
    
    context = {
        'plantaciones_con_progreso': plantaciones_con_progreso,
        'cultivos': cultivos,
        'cultivo_seleccionado': cultivo_id,
    }
    return render(request, 'plantaciones/lista_con_progreso.html', context)


# ===================================================================
# VISTA PARA EDICIÓN RÁPIDA DE FECHAS IMPORTANTES
# ===================================================================
def editar_fechas_plantacion(request, plantacion_id):
    """
    Formulario simplificado para editar solo las fechas importantes.
    Útil para actualizar rápidamente los hitos del ciclo.
    """
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    
    if request.method == 'POST':
        form = PlantacionForm(request.POST, instance=plantacion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fechas actualizadas correctamente.')
            return redirect('detalle_plantacion', plantacion_id=plantacion_id)
    else:
        form = PlantacionForm(instance=plantacion)
    
    # Mostrar solo campos de fecha
    campos_mostrar = [
        'fecha_siembra_estimada',
        'fecha_siembra_real',
        'fecha_germinado_estimado',
        'fecha_germinado_real',
        'fecha_trasplante',
        'fecha_recoleccion_inicio',
    ]
    
    context = {
        'form': form,
        'plantacion': plantacion,
        'campos_mostrar': campos_mostrar,
    }
    return render(request, 'plantaciones/editar_fechas.html', context)


# ===================================================================
# VISTA PARA REGISTRAR SIEMBRA/TRASPLANTE
# ===================================================================
def registrar_siembra(request, plantacion_id):
    """
    Registra la fecha real de siembra cuando se planta efectivamente.
    """
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    
    if request.method == 'POST':
        from django.utils import timezone
        plantacion.fecha_siembra_real = timezone.localdate()
        plantacion.save()
        messages.success(request, f'Siembra de {plantacion.cultivo.nombre} registrada.')
        return redirect('detalle_plantacion', plantacion_id=plantacion_id)
    
    return render(request, 'plantaciones/confirmar_siembra.html', {'plantacion': plantacion})


def registrar_trasplante(request, plantacion_id):
    """
    Registra la fecha de trasplante cuando se trasplanta la plántula.
    """
    plantacion = get_object_or_404(Plantacion, pk=plantacion_id)
    
    if request.method == 'POST':
        from django.utils import timezone
        plantacion.fecha_trasplante = timezone.localdate()
        plantacion.save()
        messages.success(request, f'Trasplante de {plantacion.cultivo.nombre} registrado.')
        return redirect('detalle_plantacion', plantacion_id=plantacion_id)
    
    return render(request, 'plantaciones/confirmar_trasplante.html', {'plantacion': plantacion})


# ===================================================================
# VISTA PARA COMPARAR PROGRESO DE VARIEDADES
# ===================================================================
def comparar_variedades_cultivo(request, cultivo_id):
    """
    Compara el progreso de diferentes variedades de un mismo cultivo.
    Útil para ver cuál variedad se desarrolla más rápido.
    """
    cultivo = get_object_or_404(Cultivo, pk=cultivo_id)
    
    # Obtener todas las plantaciones del cultivo no cosechadas
    plantaciones = cultivo.plantaciones.filter(cosechas__isnull=True).distinct()
    
    # Agrupar por variedad
    variedades_progreso = {}
    for plantacion in plantaciones:
        variedad_nombre = plantacion.nombre_completo
        if variedad_nombre not in variedades_progreso:
            variedades_progreso[variedad_nombre] = []
        
        progreso = plantacion.calcular_progreso_ciclo()
        variedades_progreso[variedad_nombre].append({
            'plantacion': plantacion,
            'progreso': progreso,
        })
    
    context = {
        'cultivo': cultivo,
        'variedades_progreso': variedades_progreso,
    }
    return render(request, 'plantaciones/comparar_variedades.html', context)
