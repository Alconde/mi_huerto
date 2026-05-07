from django.contrib import admin
from .models import (
    Cultivo,
    Variedad,
    Parcela,
    Plantacion,
    Tarea,
    Gasto,
    FotoHuerto,
    Cosecha,    
    HistorialRotacion,
    RecomendacionRotacion,
    FichaFrutal,
    FichaFlor,
    RemedioBotica,
    AplicacionRemedio,
)



class FichaFrutalInline(admin.StackedInline):
    model = FichaFrutal
    extra = 0
    max_num = 1


class FichaFlorInline(admin.StackedInline):
    model = FichaFlor
    extra = 0
    max_num = 1


@admin.register(Cultivo)
class CultivoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre',
        'tipo_cultivo',
        'familia',
        'emoji',
        'grupo_rotacion',
        'requiere_trasplante',
        'es_perenne',
        'epoca_siembra',
        'epoca_recoleccion',
        'dias_ciclo',
    ]
    list_filter = [
        'tipo_cultivo',
        'familia',
        'grupo_rotacion',
        'requiere_trasplante',
        'es_perenne',
    ]
    search_fields = ['nombre', 'clasificacion_rotacion', 'notas_locales']
    ordering = ['nombre']
    inlines = [FichaFrutalInline, FichaFlorInline]


@admin.register(Variedad)
class VariedadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'cultivo', 'notas_locales']
    list_filter = ['cultivo']
    search_fields = ['nombre', 'cultivo__nombre']


@admin.register(Parcela)
class ParcelaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'columnas', 'filas']
    search_fields = ['nombre']


@admin.register(Plantacion)
class PlantacionAdmin(admin.ModelAdmin):
    list_display = [
        'cultivo',
        'parcela',
        'variedad',
        'columna_inicio',
        'fila_inicio',
        'fecha_siembra',
        'tipo_siembra',
    ]
    list_filter = ['parcela', 'cultivo', 'tipo_siembra', 'fecha_siembra']
    search_fields = ['cultivo__nombre', 'parcela__nombre']
    ordering = ['-fecha_siembra']


@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'descripcion', 'fecha', 'estado_suelo', 'zona', 'completada']
    list_filter = ['tipo', 'completada', 'fecha']
    search_fields = ['descripcion', 'tipo']
    ordering = ['-fecha']


from django.contrib import admin
from .models import Gasto


@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    list_display = (
        'concepto',
        'fecha_compra',
        'categoria',
        'cantidad',
        'coste',
        'mostrar_coste_total',
        'lugar_compra',
        'es_general',
    )
    list_filter = (
        'fecha_compra',
        'categoria',
        'es_general',
    )
    search_fields = (
        'concepto',
        'lugar_compra',
        'notas',
    )
    ordering = ('-fecha_compra',)
    filter_horizontal = ('plantaciones',)

    fieldsets = (
        ('Información principal', {
            'fields': (
                'fecha_compra',
                'concepto',
                'categoria',
            )
        }),
        ('Importe y compra', {
            'fields': (
                'cantidad',
                'coste',
                'lugar_compra',
                'ticket_foto',
            )
        }),
        ('Relación con el huerto', {
            'fields': (
                'es_general',
                'plantaciones',
            )
        }),
        ('Observaciones', {
            'fields': (
                'notas',
            )
        }),
    )

    def mostrar_coste_total(self, obj):
        return f"{obj.coste_total:.2f} €"
    mostrar_coste_total.short_description = 'Total'


@admin.register(FotoHuerto)
class FotoHuertoAdmin(admin.ModelAdmin):
    list_display = ['etiqueta', 'fecha_foto', 'plantacion']
    list_filter = ['fecha_foto']
    search_fields = ['etiqueta', 'comentario']
    ordering = ['-fecha_foto']


@admin.register(Cosecha)
class CosechaAdmin(admin.ModelAdmin):
    list_display = ['plantacion', 'fecha_cosecha', 'cantidad', 'unidad', 'precio_unitario']
    list_filter = ['fecha_cosecha', 'unidad']
    search_fields = ['plantacion__cultivo__nombre']
    ordering = ['-fecha_cosecha']


@admin.register(RemedioBotica)
class RemedioBoticaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'objetivo', 'modo_aplicacion', 'activo', 'updated_at')
    list_filter = ('tipo', 'modo_aplicacion', 'activo')
    search_fields = ('nombre', 'objetivo', 'ingredientes', 'preparacion', 'notas')
    list_editable = ('activo',)


@admin.register(AplicacionRemedio)
class AplicacionRemedioAdmin(admin.ModelAdmin):
    list_display = (
        'fecha_aplicacion',
        'remedio',
        'cultivo',
        'parcela',
        'problema_detectado',
        'resultado',
        'repetir',
    )
    list_filter = ('resultado', 'repetir', 'fecha_aplicacion', 'remedio')
    search_fields = ('problema_detectado', 'dosis_aplicada', 'condiciones', 'observaciones')
    autocomplete_fields = ('remedio', 'cultivo', 'parcela')


@admin.register(HistorialRotacion)
class HistorialRotacionAdmin(admin.ModelAdmin):
    list_display = ['parcela', 'cultivo_anterior', 'cultivo_siguiente', 'fecha_rotacion']
    list_filter = ['fecha_rotacion']
    search_fields = ['parcela__nombre', 'cultivo_anterior__nombre', 'cultivo_siguiente__nombre']
    ordering = ['-fecha_rotacion']


@admin.register(RecomendacionRotacion)
class RecomendacionRotacionAdmin(admin.ModelAdmin):
    list_display = ['cultivo_actual', 'cultivo_recomendado', 'razon']
    search_fields = ['cultivo_actual__nombre', 'cultivo_recomendado__nombre']