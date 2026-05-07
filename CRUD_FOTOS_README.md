# 📸 CRUD Completo de Fotos - Guía Rápida

## ✅ Lo que se implementó

Se ha creado un **CRUD completo funcional** para la gestión de fotos del huerto con las siguientes operaciones:

### 🔵 CREATE (Crear/Subir)
**Endpoint:** `/galeria/subir/<plantacion_id>/`

- ✅ Formulario con validación
- ✅ **Drag & Drop** funcional
- ✅ Preview en tiempo real
- ✅ Selección de archivo tradicional
- ✅ Validación de tipo (debe ser imagen)
- ✅ Validación de tamaño (máx 10MB)
- ✅ Opción de marcar como hito
- ✅ Manejo automático de carpetas por fecha

**URL en template:** `{% url 'subir_foto' plantacion.id %}`

### 🟢 READ (Leer/Ver)
**Endpoints:**
- `/galeria/` - Galería general con todas las fotos
- `/galeria/plantacion/<id>/` - Línea de tiempo de una plantación
- `/galeria/foto/<id>/` - Vista detallada de una foto

- ✅ Visualización completa de fotos
- ✅ Metadatos (fecha, tipo, día del ciclo, comentarios)
- ✅ Navegación entre fotos
- ✅ Fotos relacionadas
- ✅ Filtros funcionales

### 🟡 UPDATE (Actualizar/Editar)
**Endpoint:** `/galeria/editar/<foto_id>/`

- ✅ Editar todos los campos
- ✅ Opción de reemplazar imagen
- ✅ Preview de imagen actual
- ✅ Validación de cambios
- ✅ Mantener imagen anterior si no se selecciona nueva

**URL en template:** `{% url 'editar_foto' foto.id %}`

### 🔴 DELETE (Eliminar)
**Endpoint:** `/galeria/eliminar/<foto_id>/`

- ✅ Confirmación antes de eliminar
- ✅ Preview de la foto a eliminar
- ✅ Eliminación del archivo disco + BD
- ✅ Redirección automática

**URL en template:** `{% url 'eliminar_foto' foto.id %}`

## 📋 Vistas Implementadas

### `subir_foto(request, plantacion_id)`
```python
# GET: Muestra formulario
# POST: Procesa y guarda foto
```

### `editar_foto(request, pk)`
```python
# GET: Muestra formulario con datos actuales
# POST: Procesa cambios
```

### `eliminar_foto(request, pk)`
```python
# GET: Muestra confirmación
# POST: Elimina foto
```

## 🎨 Formulario Unificado

**`FotoHuertoForm`** en `forms.py`:
- Validación automática de Django
- Widgets personalizados
- Manejo de errores
- Support para archivos

```python
class FotoHuertoForm(forms.ModelForm):
    class Meta:
        model = FotoHuerto
        fields = ['imagen', 'fecha_foto', 'etiqueta', 'comentario', 'es_hito', 'tipo_hito']
```

## 🗺️ Rutas Configuradas

```
POST   /galeria/subir/<id>/          → Nueva foto (CREATE)
GET    /galeria/subir/<id>/          → Formulario vacío (CREATE)
GET    /galeria/foto/<id>/           → Ver foto (READ)
GET    /galeria/editar/<id>/         → Formulario con datos (UPDATE)
POST   /galeria/editar/<id>/         → Guardar cambios (UPDATE)
GET    /galeria/eliminar/<id>/       → Confirmación (DELETE)
POST   /galeria/eliminar/<id>/       → Eliminar (DELETE)
```

## 🖼️ Interfaces Creadas

### 1. **formulario_foto.html**
- Usado para CREAR y EDITAR
- Drag & Drop
- Preview en tiempo real
- Validación lado cliente + servidor
- Selectores de etiqueta, fecha, comentario

### 2. **confirmar_borrado_foto.html**
- Confirmación antes de eliminar
- Preview de la foto
- Información de metadatos
- Botones de confirmación

### 3. **galeria_general.html** (actualizado)
- Botones flotantes en overlay
- Opciones: Ver, Editar, Eliminar
- Activación al pasar el ratón

### 4. **galeria_plantacion.html** (actualizado)
- 3 botones por foto: Ver, Editar, Eliminar
- Línea de tiempo funcional

### 5. **detalle_foto.html** (actualizado)
- Botones de Editar y Eliminar
- Panel lateral de acciones

## 🔐 Validaciones

- ✅ Tipo de archivo (debe ser imagen)
- ✅ Tamaño máximo (10MB)
- ✅ Campo requerido en creación
- ✅ Campo opcional en edición
- ✅ Confirmación antes de eliminar
- ✅ Relación con plantación (ForeignKey)

## 💾 Archivos Modificados

```
gestion_huerto/
├── models.py              ✓ Modelo FotoHuerto
├── views.py               ✓ +3 vistas (subir, editar, eliminar)
├── forms.py               ✓ FotoHuertoForm
├── urls.py                ✓ +2 rutas nuevas
├── admin.py               ✓ FotoHuertoAdmin
└── templates/galeria/
    ├── formulario_foto.html               ✓ NUEVO
    ├── confirmar_borrado_foto.html        ✓ NUEVO
    ├── galeria_general.html               ✓ ACTUALIZADO
    ├── galeria_plantacion.html            ✓ ACTUALIZADO
    └── detalle_foto.html                  ✓ ACTUALIZADO
```

## 🚀 Cómo Usar

### Subir una foto:
1. Ve a `/galeria/subir/<id-plantacion>/`
2. Arrastra una foto o haz clic para seleccionar
3. Completa los campos (fecha, tipo, comentario)
4. Opcionalmente marca como hito
5. Haz clic en "Guardar Foto"

### Editar una foto:
1. Ve a la vista de foto (detalle o galería)
2. Haz clic en "✏️ Editar"
3. Modifica los campos deseados
4. Puedes cambiar la imagen o mantenerla
5. Haz clic en "Guardar Foto"

### Eliminar una foto:
1. Ve a la vista de foto
2. Haz clic en "🗑️ Eliminar"
3. Confirma la eliminación
4. Se elimina la foto y el archivo

## 🔍 Acceso Rápido

Desde templates, usa:
```html
<!-- Crear -->
<a href="{% url 'subir_foto' plantacion.id %}">Nueva Foto</a>

<!-- Ver -->
<a href="{% url 'detalle_foto' foto.id %}">Ver</a>

<!-- Editar -->
<a href="{% url 'editar_foto' foto.id %}">Editar</a>

<!-- Eliminar -->
<a href="{% url 'eliminar_foto' foto.id %}">Eliminar</a>
```

## 📊 Estructura de Datos

```
FotoHuerto
├── imagen (ImageField) → media/fotos_huerto/YYYY/MM/DD/
├── fecha_subida (DateTimeField) → Auto creada
├── fecha_foto (DateField) → Editable
├── plantacion (ForeignKey) → Relación
├── etiqueta (CharField) → Categoría
├── comentario (TextField) → Descripción
├── es_hito (BooleanField) → Importante
└── tipo_hito (CharField) → Tipo de hito
```

## ✅ Check de Funcionalidad

- ✅ Subir fotos (POST con validación)
- ✅ Ver fotos (GET con filtros)
- ✅ Editar fotos (GET/POST con formulario)
- ✅ Eliminar fotos (GET confirmación + POST)
- ✅ Drag & Drop funcional
- ✅ Validación de archivos
- ✅ Gestión de cambios
- ✅ Manejo de recursos (eliminar archivos)

## 🐛 Troubleshooting

### "Error al guardar foto"
- Verifica que la imagen sea un archivo válido
- Comprueba el tamaño (máx 10MB)
- Revisa permisos en carpeta `media/`

### "No puedo editar"
- Asegúrate de que tienes acceso a la foto
- Verifica que la plantación existe
- Intenta recargar la página

### "Eliminar no funciona"
- Verifica permisos en `media/`
- Confirma la eliminación en el formulario
- Revisa consola del navegador (F12)

---

✅ **CRUD Completo Funcional** - Listo para usar en producción

