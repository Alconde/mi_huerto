# ===================================================================
# GUÍA DE IMPLEMENTACIÓN - NUEVA ESTRUCTURA DE PLANTACIÓN
# ===================================================================

## PASO 1: CREAR Y EJECUTAR LAS MIGRACIONES

Después de actualizar `models.py`, necesitas crear una migración para los nuevos campos:

```bash
python manage.py makemigrations gestion_huerto
python manage.py migrate gestion_huerto
```

Esto creará automáticamente:
- Nuevos campos en la tabla `Plantacion`:
  * fecha_siembra_estimada
  * fecha_siembra_real
  * fecha_germinado_estimado
  * fecha_germinado_real
  * fecha_recoleccion_inicio
  * Cambio de 'procedencia' de CharField a ChoiceField

- Nueva tabla `FotoPlantacion` con:
  * Referencia FK a Plantacion
  * Campo imagen (ImageField)
  * Campos de fecha, tipo_foto, días_ciclo
  * Descripción y metadatos


## PASO 2: ACTUALIZAR URLs (urls.py)

Agrega estas URLs al fichero `gestion_huerto/urls.py`:

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... URLs existentes ...
    
    # Plantaciones mejoradas
    path('plantaciones/<int:plantacion_id>/editar/', views.editar_plantacion, name='editar_plantacion'),
    path('plantaciones/<int:plantacion_id>/detalle/', views.detalle_plantacion, name='detalle_plantacion'),
    path('plantaciones/nuevo/', views.editar_plantacion, name='nueva_plantacion'),
    path('plantaciones/progreso/', views.lista_plantaciones_con_progreso, name='lista_plantaciones_progreso'),
    
    # Fotos de plantación
    path('plantaciones/<int:plantacion_id>/foto/nueva/', views.agregar_foto_plantacion, name='agregar_foto_plantacion'),
    path('plantaciones/<int:plantacion_id>/fotos/', views.galeria_fotos_plantacion, name='galeria_fotos'),
    path('fotos/<int:foto_id>/eliminar/', views.eliminar_foto_plantacion, name='eliminar_foto_plantacion'),
    
    # Edición de fechas
    path('plantaciones/<int:plantacion_id>/fechas/', views.editar_fechas_plantacion, name='editar_fechas'),
    path('plantaciones/<int:plantacion_id>/siembra/', views.registrar_siembra, name='registrar_siembra'),
    path('plantaciones/<int:plantacion_id>/trasplante/', views.registrar_trasplante, name='registrar_trasplante'),
    
    # Comparativa
    path('cultivos/<int:cultivo_id>/variedades/', views.comparar_variedades_cultivo, name='comparar_variedades'),
]
```


## PASO 3: ENTENDER EL MODELO MEJORADO

### Campos de ciclo de vida:

1. **fecha_siembra_estimada**: Cuando PLANEAS sembrar
2. **fecha_siembra_real**: Cuando REALMENTE siembras (registraste)
3. **fecha_germinado_estimado**: Cuando esperas que germine
4. **fecha_germinado_real**: Cuando germinó (registraste)
5. **fecha_trasplante**: Cuando trasplantaste la plántula
6. **fecha_recoleccion_inicio**: Cuando esperas cosechar

### Procedencia:

Ahora es un campo con opciones:
- 'semilla_propia': Para semillas que guardaste (ej: Tomate Corazón)
- 'compra_local': Para semillas compradas localmente
- 'otro': Otras procedencias

### Nuevo modelo FotoPlantacion:

Cada foto registra:
- La imagen
- Fecha de la foto
- Tipo de etapa (Germinación, Desarrollo, Floración, etc.)
- Días desde siembra (se calcula automáticamente)
- Descripción de lo observado


## PASO 4: MÉTODO calcular_progreso_ciclo()

Este método es la clave para saber el progreso actual:

```python
plantacion = Plantacion.objects.first()
progreso = plantacion.calcular_progreso_ciclo()

# Retorna un diccionario:
# {
#     'porcentaje': 45,                    # 0-100%
#     'etapa': 'Crecimiento',              # Etapa actual
#     'dias_transcurridos': 30,            # Días desde siembra
#     'dias_totales_estimados': 67         # Días totales esperados
# }
```

Úsalo en templates para:
- Mostrar barras de progreso
- Determinar qué colores usar
- Informar al usuario sobre el estado


## PASO 5: USAR EL FORMULARIO ACTUALIZADO

El nuevo `PlantacionForm` incluye:

✅ Widgets DateInput con type='date' - **Esto soluciona el bug de pérdida de datos**
✅ Inicialización correcta de valores existentes
✅ Todos los campos de ciclo de vida
✅ Validación de consistencia de variedades
✅ Validación geométrica de la parcela

**Ejemplo de uso en template:**

```html
<form method="post">
    {% csrf_token %}
    <div class="form-group">
        <label for="{{ form.fecha_siembra_estimada.id_for_label }}">Siembra Estimada</label>
        {{ form.fecha_siembra_estimada }}
    </div>
    
    <div class="form-group">
        <label for="{{ form.fecha_siembra_real.id_for_label }}">Siembra Real</label>
        {{ form.fecha_siembra_real }}
    </div>
    
    <div class="form-group">
        <label for="{{ form.fecha_trasplante.id_for_label }}">Trasplante</label>
        {{ form.fecha_trasplante }}
    </div>
    
    <button type="submit" class="btn btn-primary">Guardar</button>
</form>
```


## PASO 6: ARREGLAR EL BUG DE PÉRDIDA DE FECHAS

El problema ocurría porque:
1. Los widgets no estaban configurados con `type='date'`
2. Los valores no se inicializaban correctamente en `__init__`

**SOLUCIÓN IMPLEMENTADA:**

✅ Widgets: `forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})`
✅ En `__init__`: Inicializar valores con `self.fields['campo'].initial = valor`
✅ En vistas: `form = PlantacionForm(instance=plantacion)`

El formulario ahora:
- Carga correctamente los valores de fecha al editar
- Usa input type="date" del HTML5
- Mantiene los datos cuando se submite

**Verifica en tu formulario:**

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    if self.instance and self.instance.pk:
        # IMPORTANTE: Inicializar valores de instancia existente
        self.fields['fecha_siembra_real'].initial = self.instance.fecha_siembra_real
        self.fields['fecha_trasplante'].initial = self.instance.fecha_trasplante
        # ... etc para todos los campos
```


## PASO 7: AGREGAR AL ADMIN (OPCIONAL)

En `gestion_huerto/admin.py`, agrega:

```python
@admin.register(FotoPlantacion)
class FotoPlantacionAdmin(admin.ModelAdmin):
    list_display = ('plantacion', 'tipo_foto', 'fecha_foto', 'dias_ciclo')
    list_filter = ('tipo_foto', 'fecha_foto', 'plantacion__cultivo')
    search_fields = ('plantacion__cultivo__nombre', 'descripcion')
    readonly_fields = ('dias_ciclo',)
    
    fieldsets = (
        ('Información de foto', {
            'fields': ('plantacion', 'imagen', 'fecha_foto')
        }),
        ('Clasificación', {
            'fields': ('tipo_foto', 'dias_ciclo')
        }),
        ('Descripción', {
            'fields': ('descripcion',)
        }),
    )
```


## PASO 8: EJEMPLOS DE USO EN TEMPLATES

### Mostrar progreso:
```html
{% if plantacion.fecha_siembra_real %}
    {% with progreso=plantacion.calcular_progreso_ciclo %}
    <div class="progress">
        <div class="progress-bar" style="width: {{ progreso.porcentaje }}%">
            {{ progreso.porcentaje }}% - {{ progreso.etapa }}
        </div>
    </div>
    <small>{{ progreso.dias_transcurridos }} días de {{ progreso.dias_totales_estimados }}</small>
    {% endwith %}
{% endif %}
```

### Mostrar fotos recientes:
```html
{% for foto in plantacion.fotos_plantacion.all|slice:":6" %}
    <div class="thumbnail">
        <img src="{{ foto.imagen.url }}" alt="{{ foto.tipo_foto }}">
        <small>{{ foto.fecha_foto }} - Día {{ foto.dias_ciclo }}</small>
        <p>{{ foto.get_tipo_foto_display }}</p>
    </div>
{% endfor %}
```

### Procedencia:
```html
<p>
    Origen: 
    {% if plantacion.procedencia == 'semilla_propia' %}
        <span class="badge badge-info">Semilla Propia</span>
    {% elif plantacion.procedencia == 'compra_local' %}
        <span class="badge badge-success">Compra Local</span>
    {% endif %}
</p>
```


## PASO 9: DATOS IMPORTANTES SOBRE LA MIGRACIÓN

⚠️ **IMPORTANTE**: La migración es reversible, pero si tienes datos:

- `fecha_siembra` existentes se conservarán
- Los campos nuevos serán NULL por defecto para registros antiguos
- Puedes rellenarlos manualmente en el admin o con un script

**Script para rellenar automáticamente (opcional):**

```python
# En shell de Django: python manage.py shell
from gestion_huerto.models import Plantacion

for p in Plantacion.objects.all():
    # Si hay fecha_siembra antigua pero no fecha_siembra_real
    if p.fecha_siembra and not p.fecha_siembra_real:
        p.fecha_siembra_real = p.fecha_siembra
        p.save()
```


## PASO 10: PRÓXIMOS PASOS

1. ✅ Ejecutar migraciones
2. ✅ Actualizar URLs
3. ✅ Actualizar vistas (copiar de VISTAS_PLANTACION_MEJORADAS.py)
4. ✅ Crear templates o actualizar existentes
5. ✅ Probar edición de plantaciones
6. ✅ Agregar fotos al histórico
7. ✅ Verificar cálculo de progreso

¡Listo! Ahora tu app tiene un ciclo de vida completo de plantaciones.
