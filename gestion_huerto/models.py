# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal



FOTO_ETIQUETA_CHOICES = [
    ('GENERAL', '📸 General'),
    ('INVERNADERO', '🏠 Invernadero'),
    ('SEMILLERO', '🌱 Semillero'),
    ('PLAGA', '🐛 Plaga'),
    ('ENFERMEDAD', '🦠 Enfermedad'),
    ('COSECHA', '🥕 Cosecha'),
    ('DESARROLLO', '📈 Desarrollo'),
    ('RIEGO', '💧 Riego'),
    ('MANTENIMIENTO', '🔧 Mantenimiento'),
    ('HITO', '🏆 Hito'),
]

class Cultivo(models.Model):
    FAMILIA_CHOICES = [
        ('solanaceas',    'Solanáceas (Tomate, Pimiento, Berenjena, Patata)'),
        ('cucurbitaceas', 'Cucurbitáceas (Calabaza, Calabacín, Pepino, Melón)'),
        ('cruciferas',    'Crucíferas (Brócoli, Repollo, Coliflor, Rábano)'),
        ('hoja',          'Hoja (Lechuga, Espinaca, Acelga)'),
        ('umbeliferas',   'Umbelíferas (Zanahoria, Apio, Perejil, Hinojo)'),
        ('leguminosas',   'Leguminosas (Haba, Guisante, Judía, Alubia)'),
        ('aliaceas',      'Alíaceas (Ajo, Cebolla, Puerro, Cebolleta)'),
        ('gramineas',     'Gramíneas (Maíz, Trigo)'),
        ('compuestas',    'Compuestas (Alcachofa, Girasol)'),
        ('otros',         'Otros'),
    ]
    TIPO_CULTIVO_CHOICES = [
        ('hortaliza', 'Hortaliza'),
        ('frutal', 'Frutal'),
        ('flor', 'Flor'),
    ]
    GRUPO_ROTACION_CHOICES = [
        ('fruto', 'Grupo A — Fruto (Solanáceas, Cucurbitáceas)'),
        ('hoja_raiz', 'Grupo B — Hoja/Raíz (Crucíferas, Lechugas, Zanahorias)'),
        ('leguminosa', 'Grupo C — Leguminosa (Fija nitrógeno)'),
        ('bulbo', 'Grupo D — Bulbo/Limpieza (Aliáceas)'),
    ]

    grupo_rotacion = models.CharField(
        max_length=20,
        choices=GRUPO_ROTACION_CHOICES,
        blank=True,
        help_text="Grupo de rotación al que pertenece el cultivo"
    )
    tipo_cultivo = models.CharField(
        max_length=20,
        choices=TIPO_CULTIVO_CHOICES,
        default='hortaliza',
        help_text="Hortaliza, frutal o flor"
    )

    es_perenne = models.BooleanField(
        default=False,
        help_text="Marca si la planta permanece varios años (ej. frutales, aromáticas perennes)"
    )
    nombre = models.CharField(max_length=100, unique=True)
    familia = models.CharField(max_length=20, choices=FAMILIA_CHOICES, default='otros')
    emoji = models.CharField(max_length=10, blank=True, default='🌱')
    requiere_trasplante = models.BooleanField(default=False)
    clasificacion_rotacion = models.CharField(max_length=100, blank=True)
    epoca_siembra = models.CharField(max_length=50, blank=True)
    epoca_trasplante = models.CharField(max_length=50, blank=True)
    epoca_recoleccion = models.CharField(max_length=50, blank=True)
    dias_ciclo = models.PositiveIntegerField(null=True, blank=True)
    marco_plantacion = models.CharField(max_length=100, blank=True)
    distancia_plantas = models.PositiveIntegerField(null=True, blank=True)
    distancia_lineas = models.PositiveIntegerField(null=True, blank=True)
    profundidad_siembra = models.CharField(max_length=50, blank=True)
    meses_siembra = models.CharField(max_length=50, blank=True)
    meses_trasplante = models.CharField(max_length=50, blank=True)
    meses_recoleccion = models.CharField(max_length=50, blank=True)
    temp_min_germinacion = models.PositiveIntegerField(null=True, blank=True)
    temp_optima_germinacion = models.PositiveIntegerField(null=True, blank=True)
    temp_max_germinacion = models.PositiveIntegerField(null=True, blank=True)
    tiempo_germinacion = models.PositiveIntegerField(null=True, blank=True)
    riego = models.TextField(blank=True)
    abono = models.TextField(blank=True)
    mantenimiento = models.TextField(blank=True)
    plagas_comunes = models.TextField(blank=True)
    enfermedades_comunes = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    notas_locales = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre

    @property
    def familia_label(self):
        return self.get_familia_display()

    @property
    def familia_color(self):
        """Retorna el color hex asociado a la familia botánica"""
        color_map = {
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
        return color_map.get(self.familia, '#D3D3D3')

    NO_RIEGO_INICIAL = {
        'patata', 'patatas',
        'judia', 'judias', 'judía', 'judías',
        'maiz', 'maíz',
    }

    @property
    def meses_trasplante_lista(self):
        if not self.meses_trasplante:
            return []
        try:
            return [int(m.strip()) for m in self.meses_trasplante.split(',') if m.strip()]
        except ValueError:
            return []

    @property
    def necesita_riego_inicial(self):
        """Determina si el cultivo requiere riego desde el inicio o depende de tarea de riego."""
        if not self.nombre:
            return True

        nombre = self.nombre.strip().lower()
        nombre = nombre.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        return nombre not in self.NO_RIEGO_INICIAL
    
    class Meta:
        verbose_name = "Cultivo"
        verbose_name_plural = "Cultivos"
        ordering = ['nombre']


class Variedad(models.Model):
    nombre = models.CharField(max_length=100)
    cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='variedades')
    notas_locales = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.cultivo.nombre})"
    
    class Meta:
        verbose_name = "Variedad"
        verbose_name_plural = "Variedades"
        unique_together = ['nombre', 'cultivo']

class FichaFrutal(models.Model):
    TIPOS_POLINIZACION = [
        ('autofertil', 'Autofértil'),
        ('cruzada', 'Polinización cruzada'),
        ('desconocida', 'Desconocida'),
    ]

    TIPOS_PODA = [
        ('formacion', 'Formación'),
        ('mantenimiento', 'Mantenimiento'),
        ('fructificacion', 'Fructificación'),
        ('renovacion', 'Renovación'),
        ('sin_definir', 'Sin definir'),
    ]

    cultivo = models.OneToOneField(
        Cultivo,
        on_delete=models.CASCADE,
        related_name='ficha_frutal'
    )
    variedad_frutal = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: Golden, Starking, etc."
    )
    portainjerto = models.CharField(
        max_length=100,
        blank=True,
        help_text="Si lo conoces, anótalo"
    )
    tipo_polinizacion = models.CharField(
        max_length=20,
        choices=TIPOS_POLINIZACION,
        default='desconocida'
    )
    necesita_polinizador = models.BooleanField(
        default=False,
        help_text="Marca si necesita otro árbol compatible cerca"
    )
    marco_plantacion_m = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Marco en metros, ej: 4.00"
    )
    tipo_poda = models.CharField(
        max_length=20,
        choices=TIPOS_PODA,
        default='sin_definir'
    )
    fecha_ultima_poda = models.DateField(
        null=True,
        blank=True,
        help_text="Última poda realizada"
    )
    observaciones = models.TextField(
        blank=True,
        help_text="Notas sobre vigor, producción, problemas, etc."
    )

    def __str__(self):
        return f"Ficha frutal de {self.cultivo.nombre}"

    class Meta:
        verbose_name = "Ficha de frutal"
        verbose_name_plural = "Fichas de frutales"

class FichaFlor(models.Model):
    FUNCIONES_ECOLOGICAS = [
        ('polinizadores', 'Atracción de polinizadores'),
        ('control_plagas', 'Apoyo al control de plagas'),
        ('biodiversidad', 'Biodiversidad y refugio'),
        ('ornamental', 'Ornamental'),
        ('comestible', 'Flor comestible'),
    ]

    cultivo = models.OneToOneField(
        Cultivo,
        on_delete=models.CASCADE,
        related_name='ficha_flor'
    )
    funcion_ecologica = models.CharField(
        max_length=30,
        choices=FUNCIONES_ECOLOGICAS,
        default='biodiversidad',
        help_text="Función principal de esta flor en el huerto"
    )
    floracion_inicio_mes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Mes aproximado de inicio de floración (1-12)"
    )
    floracion_fin_mes = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Mes aproximado de fin de floración (1-12)"
    )
    atrae_polinizadores = models.BooleanField(
        default=True,
        help_text="Marca si atrae abejas y otros polinizadores"
    )
    observaciones = models.TextField(
        blank=True,
        help_text="Notas sobre asociaciones, resiembras espontáneas, etc."
    )

    def __str__(self):
        return f"Ficha flor de {self.cultivo.nombre}"

    class Meta:
        verbose_name = "Ficha de flor"
        verbose_name_plural = "Fichas de flores"

class Parcela(models.Model):
    TIPO_TABLA_CHOICES = [
        (1, 'Tabla 1 (17x12 Rectangular)'),
        (2, 'Tabla 2 (Trapezoidal 6-12m)'),
        (3, 'Tabla 3 (Irregular 12-6m)'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    columnas = models.PositiveIntegerField(default=12)
    filas = models.PositiveIntegerField(default=12)
    tipo_tabla = models.PositiveIntegerField(
        choices=TIPO_TABLA_CHOICES,
        default=1,
        help_text="Tipo de tabla para validación geométrica (1=rectangular, 2=triangular, 3=diagonal)",
    )
    foto_general = models.ImageField(upload_to='parcelas/', blank=True, null=True)
    
    def __str__(self):
        return self.nombre
    def ultima_rotacion(self):
        return self.historial_rotaciones.select_related(
            'cultivo_anterior', 'cultivo_siguiente'
        ).order_by('-fecha_rotacion').first()

    def ultimo_cultivo_historial(self):
        ultima = self.ultima_rotacion()
        if not ultima:
            return None
        return ultima.cultivo_siguiente or ultima.cultivo_anterior

    def siguiente_grupo_recomendado(self):
        orden = ['fruto', 'hoja_raiz', 'leguminosa', 'bulbo']
        ultima = self.ultima_rotacion()

        cultivo_referencia = ultima.cultivo_siguiente or ultima.cultivo_anterior if ultima else None
        if not cultivo_referencia or not cultivo_referencia.grupo_rotacion:
            return 'fruto'

        grupo_actual = cultivo_referencia.grupo_rotacion
        if grupo_actual not in orden:
            return 'fruto'

        return orden[(orden.index(grupo_actual) + 1) % len(orden)]

    class Meta:
        verbose_name = "Parcela"
        verbose_name_plural = "Parcelas"


class RotacionParcela(models.Model):
    parcela = models.ForeignKey(
        Parcela,
        on_delete=models.CASCADE,
        related_name='rotaciones'
    )
    cultivo = models.ForeignKey(
        Cultivo,
        on_delete=models.CASCADE,
        related_name='rotaciones'
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    temporada = models.CharField(max_length=50, blank=True, help_text="Ej: Primavera 2026")
    notas = models.TextField(blank=True)

    def __str__(self):
        return f"{self.parcela.nombre} → {self.cultivo.nombre} ({self.fecha_inicio})"

    def clean(self):
        if self.fecha_fin and self.fecha_fin < self.fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")

        rotaciones_misma_parcela = RotacionParcela.objects.filter(parcela=self.parcela).exclude(pk=self.pk)

        for rotacion in rotaciones_misma_parcela:
            inicio_existente = rotacion.fecha_inicio
            fin_existente = rotacion.fecha_fin or self.fecha_inicio

            nuevo_fin = self.fecha_fin or self.fecha_inicio

            if self.fecha_inicio <= fin_existente and nuevo_fin >= inicio_existente:
                raise ValidationError("Ya existe una rotación que se solapa en esta parcela.")

    @property
    def familia(self):
        return self.cultivo.familia

    @property
    def grupo_rotacion(self):
        return self.cultivo.grupo_rotacion

    class Meta:
        verbose_name = "Rotación de parcela"
        verbose_name_plural = "Rotaciones de parcelas"
        ordering = ['-fecha_inicio']

class PlantacionQuerySet(models.QuerySet):
    def activas(self):
        return self.exclude(estado__in=['finalizada', 'perdida'])
class Plantacion(models.Model):
    PROCEDENCIA_CHOICES = [
        ('semilla_propia', 'Semilla Propia'),
        ('compra_local', 'Compra Local'),
        ('ajero corella', 'Ajero Corella'),
        ('piensos muga', 'Piensos Muga'),
        ('cintruenigo', 'Cintruenigo'),
        ('otro', 'Otro'),
    ]
    
    parcela = models.ForeignKey(Parcela, on_delete=models.CASCADE, related_name='plantaciones')
    cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='plantaciones')
    variedad = models.ForeignKey(Variedad, on_delete=models.SET_NULL, null=True, blank=True, related_name='plantaciones')
    
    columna_inicio = models.PositiveIntegerField()
    fila_inicio = models.PositiveIntegerField()
    columna_fin = models.PositiveIntegerField()
    fila_fin = models.PositiveIntegerField()
    
    distancia_personalizada = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Distancia en cm entre plantas")
    precio_unitario_cosecha = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    origen_plantel = models.CharField(
        max_length=100,
        blank=True,
        help_text="Ej: semillero propio, vivero local, intercambio, etc."
    )

    observaciones_seguimiento = models.TextField(
        blank=True,
        help_text="Resumen general del seguimiento del cultivo"
    )
    TIPO_SIEMBRA_CHOICES = [
        ('terreno', 'Siembra en terreno'),
        ('semillero', 'Siembra en semillero'),
    ]
    tipo_siembra = models.CharField(
        max_length=20,
        choices=TIPO_SIEMBRA_CHOICES,
        default='terreno',
        help_text="¿Dónde se siembra? (terreno directamente o semillero para trasplantar)"
    )
    ESTADO_CHOICES = [
        ('planificada', 'Planificada'),
        ('sembrada', 'Sembrada'),
        ('germinada', 'Germinada'),
        ('trasplantada', 'Trasplantada'),
        ('en_cultivo', 'En cultivo'),
        ('en_cosecha', 'En cosecha'),
        ('finalizada', 'Finalizada'),
        ('perdida', 'Perdida'),
    ]

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='sembrada',
        help_text="Estado actual de la plantación"
    )
    # Ciclo de vida - Fechas estimadas y reales
    
    fecha_germinado_estimado = models.DateField(null=True, blank=True, help_text="Fecha prevista para la germinación")
    fecha_germinado_real = models.DateField(null=True, blank=True, help_text="Fecha en que germinó")
    
    # Para compatibilidad con código existente
    fecha_siembra = models.DateField(null=True, blank=True, help_text="Deprecated: usar fecha_siembra_real")
    fecha_trasplante = models.DateField(null=True, blank=True, help_text="Fecha de trasplante (si aplica)")
    MODO_IMPLANTACION_CHOICES = [
        ('directa', 'Siembra directa'),
        ('semillero', 'Desde semillero'),
        ('plantel', 'Plantel comprado'),
    ]

    modo_implantacion = models.CharField(
        max_length=20,
        choices=MODO_IMPLANTACION_CHOICES,
        default='directa',
        blank=False,
        verbose_name='Modo de implantación',
        help_text='Cómo entra el cultivo al terreno definitivo.'
    )
    fecha_recoleccion_inicio = models.DateField(null=True, blank=True, help_text="Fecha prevista para inicio de cosecha")
    fecha_recoleccion_esperada = models.DateField(null=True, blank=True, help_text="Deprecated: usar fecha_recoleccion_inicio")
    
    procedencia = models.CharField(
        max_length=20,
        choices=PROCEDENCIA_CHOICES,
        default='otro',
        help_text="Origen de la planta o semilla"
    )
    
    notas = models.TextField(blank=True)
    objects = PlantacionQuerySet.as_manager()
    def __str__(self):
        return f"{self.cultivo.nombre} en {self.parcela.nombre} ({self.columna_inicio}x{self.fila_inicio} - {self.columna_fin}x{self.fila_fin})"

    def archivar(self, fecha_archivo=None):
        """Marca la plantación como finalizada y guarda el cultivo en el historial de rotación."""
        if self.estado != 'finalizada':
            self.estado = 'finalizada'
            self.save(update_fields=['estado'])

        fecha_rotacion = fecha_archivo or timezone.localdate()
        HistorialRotacion.objects.create(
            parcela=self.parcela,
            cultivo_anterior=self.cultivo,
            fecha_rotacion=fecha_rotacion,
            observaciones='Archivado al finalizar el ciclo.'
        )

    @property
    def nombre_completo(self):
        if self.variedad:
            return f"{self.cultivo.nombre} ({self.variedad.nombre})"
        return self.cultivo.nombre

    def calcular_cantidad_celdas(self):
        try:
            filas = abs(self.fila_fin - self.fila_inicio) + 1
            columnas = abs(self.columna_fin - self.columna_inicio) + 1
            return filas * columnas
        except TypeError:
            return 0
    cantidad = models.PositiveIntegerField(
    null=True, blank=True,
    help_text="Número de plantas plantadas"
    )

    @property
    def fecha_plantacion(self):
        """Retorna la fecha de trasplante o siembra (para compatibilidad)"""
        return self.fecha_trasplante or self.fecha_siembra

    @property
    def fecha_cosecha_estimada(self):
        """Para compatibilidad con código existente"""
        return self.fecha_recoleccion_inicio or self.fecha_recoleccion_esperada

    @property
    def cosechada(self):
        return self.cosechas.exists()

    @property
    def cantidad_cosechada(self):
        if not self.cosechas.exists():
            return None
        return sum((c.cantidad for c in self.cosechas.all()), Decimal('0.00'))

    @property
    def unidad_cosecha(self):
        first_cosecha = self.cosechas.first()
        return first_cosecha.unidad if first_cosecha else 'uds.'

    @property
    def dias_ciclo_actual(self):
        """Calcula los días desde el inicio del ciclo hasta hoy, usando fecha de siembra, trasplante o plantación"""
        fecha_inicio = self.fecha_siembra or self.fecha_trasplante
        
        if not fecha_inicio:
            return None
        
        hoy = timezone.localdate()
        if hoy < fecha_inicio:
            return 0
    
        return (hoy - fecha_inicio).days + 1
    
    @property
    def calcular_capacidad(self):
        return self.cantidad

    @property
    def fila(self):
        return self.fila_inicio

    @property
    def columna(self):
        return self.columna_inicio

    @property
    def semaforo_estado_color(self):
        fecha = self.fecha_cosecha_estimada
        if not fecha:
            return '#6c757d'
        dias = (fecha - timezone.localdate()).days
        if dias < 0:
            return '#dc3545'
        if dias <= 7:
            return '#ffc107'
        return '#198754'

    @property
    def semaforo_estado_texto(self):
        fecha = self.fecha_cosecha_estimada
        if not fecha:
            return '#ffffff'
        dias = (fecha - timezone.localdate()).days
        if dias < 0:
            return '#ffffff'
        return '#000000' if dias <= 7 else '#ffffff'

    @property
    def etiqueta_semaforo_estado(self):
        fecha = self.fecha_cosecha_estimada
        if not fecha:
            return 'Sin fecha'
        dias = (fecha - timezone.localdate()).days
        if dias < 0:
            return 'Fecha pasada'
        if dias <= 7:
            return 'Cosecha próxima'
        return 'En curso'

    def calcular_progreso_ciclo(self):
        """
        Calcula el porcentaje de progreso del ciclo basado en las fechas estimadas/reales.
        Retorna un diccionario con:
        - porcentaje: int (0-100)
        - etapa: str (descripción de la etapa actual)
        - dias_transcurridos: int
        - dias_totales_estimados: int
        """
        hoy = timezone.localdate()
        
        # Definir el punto de inicio del ciclo con prioridad: siembra → trasplante
        inicio = self.fecha_siembra or self.fecha_trasplante
        
        if not inicio:
            return {
                'porcentaje': 0,
                'etapa': 'Sin fecha de inicio',
                'dias_transcurridos': 0,
                'dias_totales_estimados': None
            }
        
        # Si aún no ha comenzado
        if hoy < inicio:
            return {
                'porcentaje': 0,
                'etapa': 'Pendiente de inicio',
                'dias_transcurridos': 0,
                'dias_totales_estimados': self.cultivo.dias_ciclo if self.cultivo else None
            }
        
        dias_transcurridos = (hoy - inicio).days + 1
        
        # Calcular etapa y días esperados según hitos
        # Si el ciclo empezó en siembra y hay trasplante pendiente
        if self.fecha_siembra and self.fecha_trasplante and hoy < self.fecha_trasplante:
            dias_esperados = (self.fecha_trasplante - inicio).days + 1
            etapa = 'Semillero'
        # Si hay germinación estimada y aún no se alcanza
        elif self.fecha_germinado_estimado and hoy < self.fecha_germinado_estimado:
            dias_esperados = (self.fecha_germinado_estimado - inicio).days + 1
            etapa = 'Germinación'
        # Si ya se trasplantó o el inicio fue trasplante, y hay fecha de cosecha
        elif self.fecha_recoleccion_inicio:
            dias_esperados = (self.fecha_recoleccion_inicio - inicio).days + 1
            if dias_transcurridos >= dias_esperados * 0.8:
                etapa = 'Maduración'
            else:
                etapa = 'Crecimiento'
        else:
            # Usar días del cultivo o estimar 90 días
            dias_esperados = self.cultivo.dias_ciclo if (self.cultivo and self.cultivo.dias_ciclo) else 90
            etapa = 'Desarrollo general'
        
        porcentaje = min(100, int((dias_transcurridos / dias_esperados) * 100)) if dias_esperados else 0
        
        return {
            'porcentaje': porcentaje,
            'etapa': etapa,
            'dias_transcurridos': dias_transcurridos,
            'dias_totales_estimados': dias_esperados
        }

    class Meta:
        verbose_name = "Plantación"
        verbose_name_plural = "Plantaciones"
        ordering = ['-fecha_siembra']


class Tarea(models.Model):
    TIPO_CHOICES = [                 
        ('abono', 'Abono'),
        ('aporcar', 'Aporcado o escarda'),
        ('compostaje', 'Compostaje'),        
        ('cosecha', 'Cosecha'),       
        ('control_plagas', 'Control de plagas'),
        ('entutorado', 'Entutorado'),
        ('foto', 'Foto'),
        ('gallinero', 'Gallinero'),
        ('hedrar', 'Hedrado o deshierbe'),
        ('labores', 'Labores de supervisión'),        
        ('otros', 'Otros'),
        ('preparar', 'Preparar terreno'),
        ('repicado', 'Repicado'),
        ('riego', 'Riego'),
        ('siembra', 'Siembra'),
        ('trasplante', 'Trasplante'),
        ('tratamiento', 'Tratamiento'),
    ]
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    plantacion = models.ForeignKey(Plantacion, on_delete=models.CASCADE, related_name='tareas', null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(default='')
    fecha = models.DateField()
    fecha_proxima = models.DateField(null=True, blank=True)
    estado_suelo = models.CharField(max_length=100, blank=True)
    zona = models.CharField(max_length=100, blank=True)
    completada = models.BooleanField(default=False)
    plantaciones = models.ManyToManyField(Plantacion, blank=True, related_name='tareas_m2m')
    todo_el_huerto = models.BooleanField(default=False)

    tiempo_estimado_min = models.PositiveIntegerField(null=True, blank=True)
    tiempo_real_min = models.PositiveIntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.tipo} - {self.fecha}"
    
    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ['-fecha']


class Gasto(models.Model):
    CATEGORIA_CHOICES = [
        ('semillas', 'Semillas y Plantones'),
        ('abonos', 'Abonos y Compost'),
        ('herramientas', 'Herramientas'),
        ('riego', 'Sistema de Riego'),
        ('tratamientos', 'Tratamientos Ecológicos'),
        ('sustratos', 'Sustratos y Tierra'),
        ('infraestructura', 'Infraestructura'),
        ('otros', 'Otros'),
    ]

    fecha_compra = models.DateField(
        default=timezone.localdate,
        help_text='Fecha en que se realizó la compra'
    )
    concepto = models.CharField(
        max_length=200,
        default='Sin concepto',
        help_text='Descripción del producto o servicio'
    )
    categoria = models.CharField(
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default='otros',
        help_text='Categoría del gasto'
    )
    coste = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.01'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Precio unitario en euros'
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        help_text='Número de unidades compradas'
    )
    lugar_compra = models.CharField(
        max_length=100,
        default='No indicado',
        help_text='Tienda o proveedor'
    )
    notas = models.TextField(
        blank=True,
        help_text='Observaciones adicionales'
    )
    ticket_foto = models.ImageField(
        upload_to='tickets_gastos/%Y/%m/',
        blank=True,
        null=True,
        help_text='Foto del ticket de compra'
    )

    es_general = models.BooleanField(
        default=False,
        help_text="Si es True, no está asociado a plantaciones específicas"
    )
    plantaciones = models.ManyToManyField(
        'Plantacion',
        blank=True,
        related_name='gastos'
    )

    @property
    def coste_total(self):
        return self.coste * self.cantidad

    def __str__(self):
        return f"{self.concepto} - {self.fecha_compra} (€{self.coste_total})"

    class Meta:
        verbose_name = "Gasto"
        verbose_name_plural = "Gastos"
        ordering = ['-fecha_compra']

class FotoHuerto(models.Model):
    imagen = models.ImageField(
        help_text='Sube una foto de tu huerto',
        upload_to='fotos_huerto/%Y/%m/%d/'
    )
    fecha_subida = models.DateTimeField(auto_now_add=True)
    fecha_foto = models.DateField(
        default=timezone.localdate,
        help_text='Fecha en que se tomó la foto (puede ser diferente a la subida)'
    )
    etiqueta = models.CharField(
        max_length=20,
        choices=FOTO_ETIQUETA_CHOICES,
        default='GENERAL',
        help_text='Tipo de foto para filtrado'
    )
    comentario = models.TextField(
        blank=True,
        help_text='Notas sobre lo que ves en la foto (estado de la planta, plagas detectadas, etc.)'
    )
    es_hito = models.BooleanField(
        default=False,
        help_text='Marcar si es un hito importante (primera flor, primer fruto, etc.)'
    )
    tipo_hito = models.CharField(
        max_length=100,
        blank=True,
        help_text='Ej: Primera Flor, Primer Fruto, Plaga Detectada'
    )
    plantacion = models.ForeignKey(
        Plantacion,
        on_delete=models.CASCADE,
        related_name='fotos'
    )

    def __str__(self):
        return f"{self.etiqueta} - {self.fecha_foto}"

    @property
    def dia_ciclo(self):
        if self.plantacion and self.plantacion.fecha_siembra and self.fecha_foto:
            return (self.fecha_foto - self.plantacion.fecha_siembra).days + 1
        return None

    class Meta:
        verbose_name = "Foto del Huerto"
        verbose_name_plural = "Fotos del Huerto"
        ordering = ['-fecha_foto', '-fecha_subida']


class FotoPlantacion(models.Model):
    """
    Modelo para llevar un histórico fotográfico de cada plantación
    a lo largo de su ciclo de vida.
    """

    TIPO_FOTO_CHOICES = [
        ('germinacion', 'Germinación'),
        ('primer_brote', 'Primer brote'),
        ('desarrollo', 'Desarrollo'),
        ('floracion', 'Floración'),
        ('cuajado', 'Cuajado'),
        ('maduracion', 'Maduración'),
        ('cosecha', 'Cosecha'),
        ('plagas', 'Plagas/Enfermedades'),
        ('hito', 'Hito importante'),
        ('otro', 'Otro'),
    ]

    plantacion = models.ForeignKey(
        'Plantacion',
        on_delete=models.CASCADE,
        related_name='fotos_plantacion'
    )
    imagen = models.ImageField(
        upload_to='fotos_plantacion/%Y/%m/%d/',
        help_text='Foto del estado de la plantación'
    )
    fecha_foto = models.DateField(
        default=timezone.localdate,
        help_text='Fecha en que se tomó la foto'
    )
    tipo_foto = models.CharField(
        max_length=20,
        choices=TIPO_FOTO_CHOICES,
        default='desarrollo',
        help_text='Etapa de desarrollo cuando se tomó la foto'
    )
    dias_ciclo = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Días desde la siembra cuando se tomó la foto'
    )
    descripcion = models.TextField(
        blank=True,
        help_text='Notas sobre el estado observado, cambios, plagas detectadas, etc.'
    )
    fecha_subida = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Foto {self.plantacion.nombre_completo} - {self.fecha_foto}"

    def save(self, *args, **kwargs):
        # Usar fecha de siembra o trasplante como inicio del ciclo
        fecha_inicio = self.plantacion.fecha_siembra or self.plantacion.fecha_trasplante

        if self.dias_ciclo in (None, 0) and fecha_inicio and self.fecha_foto:
            self.dias_ciclo = (self.fecha_foto - fecha_inicio).days + 1

        super().save(*args, **kwargs)

class Cosecha(models.Model):
    UNIDAD_CHOICES = [
        ('kg', 'Kilogramos'),
        ('u', 'Unidades'),
        ('cajas', 'Cajas'),
        ('otros', 'Otros'),
    ]
    
    plantacion = models.ForeignKey(Plantacion, on_delete=models.CASCADE, related_name='cosechas')
    fecha_cosecha = models.DateField(default=timezone.localdate)
    cantidad = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    unidad = models.CharField(max_length=10, choices=UNIDAD_CHOICES, default='kg')
    precio_unitario = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Precio de mercado por unidad'
    )
    notas = models.TextField(blank=True)
    
    @property
    def total(self):
        if self.precio_unitario:
            return self.cantidad * self.precio_unitario
        return Decimal('0.00')

    @property
    def valor_total(self):
        return self.total
    
    def __str__(self):
        return f"Cosecha de {self.plantacion.cultivo.nombre} - {self.fecha_cosecha}"
    
    class Meta:
        verbose_name = "Cosecha"
        verbose_name_plural = "Cosechas"
        ordering = ['-fecha_cosecha', '-id']


class RemedioBotica(models.Model):
    class TipoRemedio(models.TextChoices):
        INSECTICIDA = 'insecticida', 'Insecticida'
        FUNGICIDA = 'fungicida', 'Fungicida'
        BIOESTIMULANTE = 'bioestimulante', 'Bioestimulante'
        FERTILIZANTE = 'fertilizante', 'Fertilizante'
        REPELENTE = 'repelente', 'Repelente'
        CICATRIZANTE = 'cicatrizante', 'Cicatrizante'
        OTRO = 'otro', 'Otro'

    class Aplicacion(models.TextChoices):
        FOLIAR = 'foliar', 'Aplicación foliar'
        SUELO = 'suelo', 'Aplicación al suelo'
        RIEGO = 'riego', 'En agua de riego'
        PINCELADO = 'pincelado', 'Pincelado localizado'
        TRAMPA = 'trampa', 'Trampa o cebo'
        OTRO = 'otro', 'Otro'

    nombre = models.CharField(max_length=120, unique=True)
    tipo = models.CharField(
        max_length=20,
        choices=TipoRemedio.choices,
        default=TipoRemedio.OTRO,
    )
    objetivo = models.CharField(
        max_length=200,
        help_text='Ej: pulgón, oídio, mildiu, vigor, prevención...'
    )
    ingredientes = models.TextField()
    preparacion = models.TextField()
    dosis = models.CharField(
        max_length=200,
        blank=True,
        help_text='Ej: 10 ml/L, 100 g por 5 L, diluir al 20%...'
    )
    modo_aplicacion = models.CharField(
        max_length=20,
        choices=Aplicacion.choices,
        default=Aplicacion.FOLIAR,
    )
    periodicidad = models.CharField(
        max_length=200,
        blank=True,
        help_text='Ej: cada 7 días, tras lluvias, solo preventivo...'
    )
    momento_ideal = models.CharField(
        max_length=200,
        blank=True,
        help_text='Ej: al atardecer, sin viento, evitar horas de sol fuerte.'
    )
    advertencias = models.TextField(
        blank=True,
        help_text='Precauciones, incompatibilidades, riesgo de fitotoxicidad...'
    )
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Remedio de botica'
        verbose_name_plural = 'Remedios de botica'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def get_absolute_url(self):
        return reverse('detalle_remedio_botica', kwargs={'pk': self.pk})




class AplicacionRemedio(models.Model):
    class Resultado(models.TextChoices):
        MUY_BUENO = 'muy_bueno', 'Muy bueno'
        BUENO = 'bueno', 'Bueno'
        REGULAR = 'regular', 'Regular'
        BAJO = 'bajo', 'Bajo'
        SIN_CAMBIOS = 'sin_cambios', 'Sin cambios'

    remedio = models.ForeignKey(
        'RemedioBotica',
        on_delete=models.CASCADE,
        related_name='aplicaciones'
    )
    fecha_aplicacion = models.DateField()
    cultivo = models.ForeignKey(
        'Cultivo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aplicaciones_remedios'
    )
    parcela = models.ForeignKey(
        'Parcela',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aplicaciones_remedios'
    )
    problema_detectado = models.CharField(
        max_length=200,
        help_text='Ej: pulgón, mildiu, prevención, debilitamiento...'
    )
    dosis_aplicada = models.CharField(
        max_length=200,
        blank=True,
        help_text='Ej: 12 ml/L, pulverización fina al atardecer'
    )
    condiciones = models.CharField(
        max_length=200,
        blank=True,
        help_text='Ej: tarde húmeda, tras lluvia, calor suave...'
    )
    resultado = models.CharField(
        max_length=20,
        choices=Resultado.choices,
        blank=True
    )
    repetir = models.BooleanField(default=False)
    tarea_seguimiento = models.ForeignKey(
        'Tarea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='aplicaciones_botica',
        help_text='Tarea generada automáticamente para revisar el efecto de esta aplicación'
    )
    observaciones = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Aplicación de remedio'
        verbose_name_plural = 'Aplicaciones de remedios'
        ordering = ['-fecha_aplicacion', '-id']

    def __str__(self):
        return f'{self.remedio.nombre} - {self.fecha_aplicacion}'

    def get_absolute_url(self):
        return reverse('detalle_remedio_botica', kwargs={'pk': self.remedio.pk})

class HistorialRotacion(models.Model):
    parcela = models.ForeignKey(Parcela, on_delete=models.CASCADE, related_name='historial_rotaciones')
    cultivo_anterior = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='rotaciones_anteriores', null=True, blank=True)
    cultivo_siguiente = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='rotaciones_siguientes', null=True, blank=True)
    fecha_rotacion = models.DateField()
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        anterior = self.cultivo_anterior.nombre if self.cultivo_anterior else "Sin anterior"
        siguiente = self.cultivo_siguiente.nombre if self.cultivo_siguiente else "Sin siguiente"
        return f"Rotación en {self.parcela.nombre}: {anterior} → {siguiente}"
    
    class Meta:
        verbose_name = "Historial de Rotación"
        verbose_name_plural = "Historial de Rotaciones"
        ordering = ['-fecha_rotacion']


class RecomendacionRotacion(models.Model):
    cultivo_actual = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='recomendaciones_actual', null=True, blank=True)
    cultivo_recomendado = models.ForeignKey(Cultivo, on_delete=models.CASCADE, related_name='recomendaciones_siguiente', null=True, blank=True)
    razon = models.TextField(default='')
    
    def __str__(self):
        actual = self.cultivo_actual.nombre if self.cultivo_actual else "Sin actual"
        recomendado = self.cultivo_recomendado.nombre if self.cultivo_recomendado else "Sin recomendado"
        return f"Recomendación: después de {actual} → {recomendado}"
    class Meta:
        verbose_name = "Recomendación de Rotación"
        verbose_name_plural = "Recomendaciones de Rotación"
        unique_together = ['cultivo_actual', 'cultivo_recomendado']