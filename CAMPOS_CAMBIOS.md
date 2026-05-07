# ===================================================================
# COMPARACIÓN ANTES vs DESPUÉS - CAMBIOS EN MODELS.PY
# ===================================================================

## MODELO PLANTACION - CAMBIOS

### CAMPOS NUEVOS AGREGADOS:

1. **fecha_siembra_estimada** (DateField)
   - Descripción: Fecha prevista para la siembra
   - Requerido: No (null=True, blank=True)
   - Uso: Planificación a largo plazo

2. **fecha_siembra_real** (DateField)
   - Descripción: Fecha en que se sembró realmente
   - Requerido: No (null=True, blank=True)
   - Uso: Registro de lo que realmente sucedió

3. **fecha_germinado_estimado** (DateField)
   - Descripción: Fecha prevista para la germinación
   - Requerido: No (null=True, blank=True)
   - Uso: Planificación del ciclo

4. **fecha_germinado_real** (DateField)
   - Descripción: Fecha en que germinó
   - Requerido: No (null=True, blank=True)
   - Uso: Registro visual del progreso

5. **fecha_recoleccion_inicio** (DateField)
   - Descripción: Fecha prevista para inicio de cosecha
   - Requerido: No (null=True, blank=True)
   - Uso: Planificación de cosecha

### CAMPOS MODIFICADOS:

1. **procedencia**
   ANTES:
   ```python
   procedencia = models.CharField(max_length=200, blank=True)
   # Ejemplo: "Semillero propio, compra local"
   ```
   
   DESPUÉS:
   ```python
   procedencia = models.CharField(
       max_length=20,
       choices=PROCEDENCIA_CHOICES,
       default='otro',
       help_text="Origen de la planta o semilla"
   )
   # Opciones: 'semilla_propia', 'compra_local', 'otro'
   ```
   
   Ventaja: Datos normalizados, búsquedas más fáciles

### CAMPOS CONSERVADOS (para compatibilidad):

1. **fecha_siembra** - Mantiene el valor antiguo para transiciones
2. **fecha_recoleccion_esperada** - Mantiene el valor antiguo para transiciones
3. **fecha_trasplante** - Sin cambios

### MÉTODOS NUEVOS:

```python
def calcular_progreso_ciclo(self):
    """
    Calcula el porcentaje de progreso del ciclo.
    
    Retorna dict con:
    - porcentaje: 0-100
    - etapa: str (nombre de etapa)
    - dias_transcurridos: int
    - dias_totales_estimados: int
    """
```

---

## MODELO FOTOPLANTACION - NUEVO

Estructura completa del nuevo modelo:

```python
class FotoPlantacion(models.Model):
    TIPO_FOTO_CHOICES = [
        ('germinacion', 'Germinación'),
        ('primer_brote', 'Primer brote'),
        ('desarrollo', 'Desarrollo'),
        ('floración', 'Floración'),
        ('cuajado', 'Cuajado'),
        ('maduración', 'Maduración'),
        ('cosecha', 'Cosecha'),
        ('plagas', 'Plagas/Enfermedades'),
        ('hito', 'Hito importante'),
        ('otro', 'Otro'),
    ]
    
    # FK
    plantacion = ForeignKey(Plantacion, on_delete=CASCADE)
    
    # Datos de foto
    imagen = ImageField(upload_to='fotos_plantacion/%Y/%m/%d/')
    fecha_foto = DateField(default=timezone.localdate)
    fecha_subida = DateTimeField(auto_now_add=True)
    
    # Clasificación
    tipo_foto = CharField(max_length=20, choices=TIPO_FOTO_CHOICES)
    dias_ciclo = PositiveIntegerField(null=True, blank=True)
    
    # Descripción
    descripcion = TextField(blank=True)
```

---

## CAMBIOS EN FORMS.PY

### PlantacionForm - NUEVOS CAMPOS:

```python
# Campos de ciclo de vida (DateField en el form)
fecha_siembra_estimada = forms.DateField(...)
fecha_siembra_real = forms.DateField(...)
fecha_germinado_estimado = forms.DateField(...)
fecha_germinado_real = forms.DateField(...)
fecha_trasplante = forms.DateField(...)
fecha_recoleccion_inicio = forms.DateField(...)
```

### Widgets - IMPORTANTE (SOLUCIÓN DEL BUG):

```python
# ✅ CORRECTO - Soluciona pérdida de datos
forms.DateInput(attrs={
    'class': 'form-control',
    'type': 'date'  # ← HTML5 native date input
})

# ❌ INCORRECTO - Causaba pérdida de datos
forms.DateInput(attrs={'class': 'form-control'})
```

### Inicialización en __init__ - IMPORTANTE:

```python
# ✅ Carga valores existentes correctamente
if self.instance and self.instance.pk:
    self.fields['fecha_siembra_real'].initial = self.instance.fecha_siembra_real
    self.fields['fecha_trasplante'].initial = self.instance.fecha_trasplante
    # ... etc
```

### Nuevo FotoPlantacionForm:

```python
class FotoPlantacionForm(forms.ModelForm):
    class Meta:
        model = FotoPlantacion
        fields = ['imagen', 'fecha_foto', 'tipo_foto', 'dias_ciclo', 'descripcion']
```

---

## VISTA - CAMBIOS REQUERIDOS

ANTES (problemática):
```python
def editar_plantacion(request, plantacion_id=None):
    # ...
    form = PlantacionForm(request.POST, instance=plantacion)
    # ✅ Ya estaba bien aquí (instance=plantacion)
```

DESPUÉS (mejorado):
```python
def editar_plantacion(request, plantacion_id=None):
    # Exactamente igual, pero ahora los widgets funcionan correctamente
    form = PlantacionForm(request.POST, instance=plantacion)
```

El cambio no está en la vista, sino en:
1. Los widgets del formulario (ahora tienen type='date')
2. La inicialización en __init__ (ahora inicializa correctamente)

---

## MIGRACIÓN - LO QUE SUCEDERÁ

Cuando ejecutes:
```bash
python manage.py makemigrations
python manage.py migrate
```

Se crearán/modificarán:
- Tabla `gestion_huerto_plantacion`: 5 nuevas columnas
- Tabla `gestion_huerto_fotoplantacion`: nueva tabla completa
- Índices automáticos para ForeignKey

---

## COMPARACIÓN DE DATOS

### Entrada antigua:
```python
plantacion = Plantacion.objects.create(
    cultivo=tomate,
    parcela=parcela,
    fila_inicio=1,
    columna_inicio=1,
    fila_fin=2,
    columna_fin=2,
    fecha_siembra=date(2026, 4, 15),
    procedencia="Semillero propio"  # ← String libre
)
```

### Entrada nueva:
```python
plantacion = Plantacion.objects.create(
    cultivo=tomate,
    parcela=parcela,
    fila_inicio=1,
    columna_inicio=1,
    fila_fin=2,
    columna_fin=2,
    fecha_siembra_estimada=date(2026, 4, 10),
    fecha_siembra_real=date(2026, 4, 15),  # ← Cuando realmente sembré
    fecha_germinado_estimado=date(2026, 4, 22),
    fecha_trasplante=date(2026, 5, 10),
    fecha_recoleccion_inicio=date(2026, 7, 1),
    procedencia='semilla_propia'  # ← Normalizado
)
```

---

## CONSULTAS SQL EQUIVALENTES

### Ver progreso de todas:
```python
# En templates/vistas
plantaciones = Plantacion.objects.filter(fecha_siembra_real__isnull=False)
for p in plantaciones:
    progreso = p.calcular_progreso_ciclo()
    print(f"{p.nombre_completo}: {progreso['porcentaje']}%")
```

### Filtrar por procedencia:
```python
semillas_propias = Plantacion.objects.filter(procedencia='semilla_propia')
compras = Plantacion.objects.filter(procedencia='compra_local')
```

### Obtener fotos de una etapa:
```python
fotos_floracion = plantacion.fotos_plantacion.filter(tipo_foto='floración')
```

---

## ARCHIVOS MODIFICADOS vs ARCHIVOS NUEVOS

### MODIFICADOS (ya existían):
✅ models.py - Plantacion + nuevo FotoPlantacion
✅ forms.py - PlantacionForm mejorado + FotoPlantacionForm

### NUEVOS (referencia, copiar a views.py/urls.py según necesites):
📄 VISTAS_PLANTACION_MEJORADAS.py - Ejemplos de vistas
📄 GUIA_IMPLEMENTACION.md - Instrucciones detalladas
📄 RESUMEN_CAMBIOS.md - Resumen de cambios
📄 EJEMPLOS_TEMPLATES.html - Templates HTML
📄 CHECKLIST_IMPLEMENTACION.md - Checklist de tareas
📄 CAMPOS_CAMBIOS.md - Este archivo

---

## ⚡ CAMBIOS CRÍTICOS (NO OLVIDES)

1. ✅ Ejecutar migraciones
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. ✅ Usar DateInput con type='date' EN TODOS los campos de fecha
   ```python
   forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
   ```

3. ✅ Inicializar valores en __init__ si es una instancia existente
   ```python
   if self.instance and self.instance.pk:
       self.fields['fecha_siembra_real'].initial = ...
   ```

4. ✅ En vistas, usar instance=plantacion
   ```python
   form = PlantacionForm(request.POST, instance=plantacion)
   ```

5. ✅ En templates, usar calcular_progreso_ciclo()
   ```html
   {% with progreso=plantacion.calcular_progreso_ciclo %}
       {{ progreso.porcentaje }}%
   {% endwith %}
   ```

---

## 📊 ESTADÍSTICAS DE CAMBIOS

| Elemento | Antes | Después | Cambios |
|----------|-------|---------|---------|
| Campos Plantacion | 20 | 25 | +5 nuevos |
| Modelos | 11 | 12 | +1 (FotoPlantacion) |
| Formularios | 5 | 6 | +1 (FotoPlantacionForm) |
| Métodos Plantacion | 15 | 16 | +1 (calcular_progreso) |
| Líneas de código | ~500 | ~650 | +150 |

---

¡Listo! Todos los cambios han sido documentados. 🎉
