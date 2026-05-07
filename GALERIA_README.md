# 📸 Sistema de Galería - Mi Huerto

## Descripción General

Se ha creado un **sistema completo de galería transversal** que permite documentar la evolución visual de tu huerto mediante fotos organizadas por plantación.

## ✨ Características Principales

### 1. **Modelo FotoHuerto** (`models.py`)
- **Campo de imagen**: Con almacenamiento automático en `media/fotos_huerto/YYYY/MM/DD/`
- **Relación ForeignKey** a Plantación
- **Etiquetas**: 10 tipos para clasificar fotos:
  - 📸 General
  - 🏠 Invernadero
  - 🌱 Semillero
  - 🐛 Plaga
  - 🦠 Enfermedad
  - 🥕 Cosecha
  - 📈 Desarrollo
  - 💧 Riego
  - 🔧 Mantenimiento
  - 🏆 Hito

- **Campos adicionales**:
  - `fecha_foto`: Fecha en que se tomó (no necesariamente la de subida)
  - `comentario`: Notas sobre el estado de la planta
  - `es_hito`: Booleano para marcar hitos importantes
  - `tipo_hito`: Descripción del hito (Primera Flor, Primer Fruto, Plaga, etc.)

### 2. **Vistas (`views.py`)**

#### `galeria_general(request)`
- **URL**: `/galeria/`
- **Descripción**: Galería principal con TODAS las fotos
- **Características**:
  - Grid tipo "masonry" estilo Pinterest
  - Filtros por: etiqueta, cultivo, hitos
  - Vista de 250x250 con preview de imagen

#### `galeria_plantacion(request, pk)`
- **URL**: `/galeria/plantacion/<id>/`
- **Descripción**: Línea de tiempo visual de UNA plantación
- **Características**:
  - Muestra fotos en orden cronológico
  - Alternancia izquierda-derecha (estilo timeline)
  - Información del "día del ciclo"
  - Indicador de hitos con emoji 🏆
  - Botón para subir nuevas fotos

#### `subir_foto(request, plantacion_id)`
- **URL**: `/galeria/subir/<plantacion_id>/`
- **Descripción**: Formulario para subir fotos
- **Características**:
  - ✅ **Drag & Drop**: Arrastra fotos directamente
  - Click para seleccionar
  - Preview en tiempo real
  - Opción de marcar como "hito"
  - Ajuste de fecha (para fotos antiguas)

#### `detalle_foto(request, pk)`
- **URL**: `/galeria/foto/<id>/`
- **Descripción**: Vista ampliada de una foto
- **Características**:
  - Imagen a tamaño completo
  - Panel lateral con metadatos
  - Navegación entre fotos (anterior/siguiente)
  - Fotos relacionadas de la misma plantación

### 3. **Templates Creados**

#### `/galeria/galeria_general.html`
- Grid masonry responsivo (auto-fill minmax)
- Filtros funcionales
- Tarjetas con información rápida
- Acceso a vista detallada

#### `/galeria/galeria_plantacion.html`
- Timeline al estilo blog (alternancia)
- Botón flotante para subir fotos
- Vista de evolución cronológica
- Detalles por día del ciclo

#### `/galeria/subir_foto.html`
- Formulario con drag & drop
- JavaScript interactivo para preview
- Mostrar/ocultar opciones de hito
- Diseño mobile-friendly

#### `/galeria/detalle_foto.html`
- Imagen ampliada
- Panel con metadatos
- Navegación left/right
- Galería de miniaturas relacionadas

### 4. **URLs Configuradas**

```
/galeria/                          → Galería general (todas las fotos)
/galeria/plantacion/<id>/          → Línea de tiempo de una plantación
/galeria/subir/<plantacion_id>/    → Formulario para subir foto
/galeria/foto/<id>/                → Vista detallada de una foto
```

### 5. **Admin**

Registrado con clase `FotoHuertoAdmin` personalizada:
- Vista previa de miniaturas
- Filtros por etiqueta, cultivo, hito, fecha
- Vista de imagen en el admin
- Búsqueda por cultivo y comentario
- Jerarquía de fechas (date_hierarchy)

## 🔧 Configuración

### Dependencias
- ✅ **Pillow**: Ya instalado (para manejo de imágenes)
- ✅ **Django 6.0+**: Ya configurado

### Settings.py
Ya configurado en tu proyecto:
```python
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### URLs principal (`huerto_proyecto/urls.py`)
Ya configurado para servir medias en desarrollo:
```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## 📱 Cómo Usar

### Paso 1: Subir una foto
1. Ve a la ficha de una plantación
2. Haz clic en "📸 Nueva Foto" o ve a `galeria/subir/ID_PLANTACION/`
3. Arrastra una foto o haz clic para seleccionar
4. Agrega una nota (opcional)
5. Marca como "hito" si es importante
6. ¡Listo! La foto se guardará automáticamente

### Paso 2: Ver evolución
1. Entra a la ficha de la plantación
2. Ve a "Evolución Visual" (en `galeria/plantacion/ID/`)
3. Verás todas las fotos en timeline
4. El sistema automáticamente calcula "Día del ciclo"

### Paso 3: Explorar la galería
1. Haz clic en "📸 Galería" en el menú
2. Filtra por cultivo, tipo de foto, o solo hitos
3. Haz clic en una foto para ampliarla
4. Navega entre fotos con anterior/siguiente

## 🎨 Características de Diseño

- ✅ **Colores del huerto**: Verdes, tierra, agua
- ✅ **Responsive**: Funciona en móvil y escritorio
- ✅ **Drag & Drop**: Experiencia intuitiva
- ✅ **Timeline visual**: Alternancia de fotos
- ✅ **Masonry Grid**: Adaptable a cualquier tamaño
- ✅ **Iconos emoji**: Fácil identificación visual

## 🚀 Ideas Futuras Implementables

### De tu lista:
1. **✅ Galería transversal**: ✓ Hecha
2. **✅ Subida rápida desde móvil**: ✓ Formulario con drag & drop
3. **✅ Línea de tiempo por plantación**: ✓ Vista `galeria_plantacion`
4. **✅ Visualizador Antes/Después**: Listo para implementar (ya tenemos navegación)
5. **⏳ GPS automático**: Requiere `exifread` (opcional)
6. **⏳ Hitos con notificaciones**: Requiere celery/signals
7. **⏳ Iconos de cámara en el plano**: Requiere actualizar `mapa_huerto.html`

## 📂 Estructura de Carpetas

```
media/
├── fotos_huerto/
│   ├── 2026/
│   │   ├── 04/
│   │   │   ├── 05/
│   │   │   │   ├── foto_12345.jpg
```

Las fotos se organizan automáticamente por: `YYYY/MM/DD/`

## 🔐 Seguridad

- Las imágenes se suben a través de MediaField de Django (seguro)
- Se redimensionan automáticamente (Pillow)
- Las URLs de media solo funcionan en `/media/`

## 💾 Base de Datos

Nueva migración creada:
- `0016_alter_tarea_tipo_fotohuerto.py`
- Incluye: Cambio de tipos de tarea + Modelo FotoHuerto

Ejecutada correctamente ✅

## 📞 Troubleshooting

### "Las fotos no se visualizan"
1. Asegúrate de que la carpeta `media/` existe
2. Verifica que `DEBUG = True` en settings.py
3. Comprueba que las URLs están configuradas

### "No puedo subir fotos"
1. Verifica permisos de escritura en carpeta `media/`
2. Asegúrate de que Pillow está instalado
3. Espacio suficiente en disco

### "Las fotos se ven cortadas"
Las imágenes se visualizan con `object-fit: cover` para mantener aspecto. Es normal que se recorten.

## 📊 Próximos Pasos Sugeridos

1. **Probar la galería**: Sube algunas fotos de prueba
2. **Personalizar etiquetas**: Modifica `ETIQUETAS_FOTO` en `models.py` si lo necesitas
3. **Agregar comparador antes/después**: Ya hay la estructura en vistas
4. **Añadir iconos al plano**: Muestra 📷 en celdas con fotos recientes

---

¡Tu galería está lista para capturar la historia visual de tu huerto! 📸🌿
