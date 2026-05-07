# 🧪 MANUAL DE TESTING - CRUD DE FOTOS

## ✅ Verificación: Todas las URLs Funcionan

```
✓ /galeria/                       → Galería general
✓ /galeria/plantacion/1/          → Línea de tiempo de plantación
✓ /galeria/subir/1/               → Subir foto
✓ /galeria/foto/1/                → Ver foto detallada
✓ /galeria/editar/1/              → Editar foto
✓ /galeria/eliminar/1/            → Eliminar foto
```

---

## 🚀 Cómo Probar (Paso a Paso)

### PASO 1: Preparar Datos

```bash
# Acceder al shell de Django
python manage.py shell

# Crear una plantación de prueba (si no existe)
from gestion_huerto.models import Cultivo, Parcela, Plantacion
from datetime import date

cultivo = Cultivo.objects.first()  # O crear uno
parcela = Parcela.objects.first()  # O crear uno

plantacion = Plantacion.objects.create(
    cultivo=cultivo,
    parcela=parcela,
    fecha_plantacion=date.today(),
    fecha_cosecha_estimada=date.today(),
    cantidad=10,
    fila_inicio=1,
    fila_fin=1,
    columna_inicio=1,
    columna_fin=1,
)

print(f"✓ Plantación creada: ID={plantacion.id}")
```

### PASO 2: Iniciar Servidor

```bash
python manage.py runserver
```

Accede a: http://localhost:8000

### PASO 3: Probar CREATE (Subir Foto)

1. Navega a: `http://localhost:8000/galeria/subir/1/`
2. Deberías ver el formulario
3. Prueba:
   - ✅ Drag & Drop una imagen
   - ✅ Click para seleccionar
   - ✅ Completa campos
   - ✅ Marca como hito
   - ✅ Click "Guardar Foto"

**Verificación:**
- [ ] La foto se carga
- [ ] Aparece en galería
- [ ] Se guarda en `media/fotos_huerto/`
- [ ] Redirige a plantación

### PASO 4: Probar READ (Ver Fotos)

1. **Galería General:** `http://localhost:8000/galeria/`
   - [ ] Ves todas las fotos
   - [ ] Filtros funcionan
   - [ ] Botones de acción aparecen al pasar ratón

2. **Línea de Tiempo:** `http://localhost:8000/galeria/plantacion/1/`
   - [ ] Ves timeline de la plantación
   - [ ] Fotos ordenadas por fecha
   - [ ] Información de día del ciclo

3. **Detalle:** `http://localhost:8000/galeria/foto/1/`
   - [ ] Foto ampliada
   - [ ] Metadatos completos
   - [ ] Navegación anterior/siguiente
   - [ ] Fotos relacionadas

### PASO 5: Probar UPDATE (Editar Foto)

1. Click en "✏️ Editar" (desde cualquier vista)
2. O accede a: `http://localhost:8000/galeria/editar/1/`
3. Prueba:
   - [ ] Modificar fecha
   - [ ] Cambiar etiqueta
   - [ ] Editar comentario
   - [ ] Cambiar hito
   - [ ] Reemplazar imagen (opcional)
   - [ ] Click "Guardar Foto"

**Verificación:**
- [ ] Los cambios se guardan
- [ ] La foto se actualiza en galería
- [ ] Redirige a detalle

### PASO 6: Probar DELETE (Eliminar Foto)

1. Click en "🗑️ Eliminar" (desde cualquier vista)
2. O accede a: `http://localhost:8000/galeria/eliminar/1/`
3. Deberías ver:
   - [ ] Preview de la foto
   - [ ] Confirmación
   - [ ] Botones de acción

4. Click "Sí, Eliminar"

**Verificación:**
- [ ] Foto se elimina BD
- [ ] Archivo se elimina del disco
- [ ] Redirige a galería plantación
- [ ] Ya no aparece en listados

---

## 🔍 Validaciones a Probar

### Validación de Archivo

```bash
1. Intenta subir un archivo que NO es imagen
   ✗ ERROR: "Debe ser una imagen"

2. Intenta subir una imagen > 10MB
   ✗ ERROR: "Imagen demasiado grande"

3. Intenta el drag & drop sin archivo
   ✗ Botón deshabilitado o error
```

### Validación de Campos

```bash
1. Intenta crear foto sin imagen
   ✗ ERROR: Campo requerido

2. Edita foto sin cambiar imagen
   ✓ OK: Mantiene imagen anterior

3. Intenta eliminar sin confirmar
   ✗ ERROR: Necesita confirmación
```

---

## 📊 Checklist Completo

### Funcionalidad
- [ ] Crear foto con drag & drop
- [ ] Crear foto con click
- [ ] Preview antes de guardar
- [ ] Ver todas las fotos
- [ ] Filtrar fotos
- [ ] Ver foto en detalle
- [ ] Navegar entre fotos
- [ ] Editar todos los campos
- [ ] Reemplazar imagen
- [ ] Eliminar con confirmación

### UI/UX
- [ ] Botones flotantes en galería
- [ ] Botones en timeline
- [ ] Panel de acciones
- [ ] Formulario responsive
- [ ] Confirmación visual
- [ ] Errores claros
- [ ] Redirecciones correctas

### Técnico
- [ ] URLs funcionan (6/6)
- [ ] Formulario valida
- [ ] Archivos se guardan
- [ ] BD se actualiza
- [ ] Archivos se eliminan
- [ ] No hay errores (check)

---

## 🐛 Debugging

Si algo no funciona:

### "404 en URL"
```
❌ /galeria/editar/1/ dice 404
✓ Solución: Verifica que URLs están en urls.py
✓ Verifica nombre en {% url %}
```

### "Error de validación"
```
❌ Dice "Campo requerido" incluso con imagen
✓ Solución: Revisa console (F12) por errores JS
✓ Verifica tipo MIME del archivo
```

### "Foto no se guarda"
```
❌ Aparece sin errores pero no está en BD
✓ Solución: Verifica BD en admin
✓ Revisa permisos en media/
```

### "No puedo eliminar"
```
❌ Botón no funciona
✓ Solución: POST debe ser POST (no GET)
✓ Verifica punto de vista eliminar_foto
```

---

## 🧪 Test de Carga

Para probar con múltiples fotos:

```python
# En shell de Django
from gestion_huerto.models import FotoHuerto, Plantacion
from django.core.files.base import ContentFile
from PIL import Image
import io

plantacion = Plantacion.objects.first()

for i in range(10):
    # Crear imagen de prueba
    img = Image.new('RGB', (100, 100), color='red')
    img_io = io.BytesIO()
    img.save(img_io, 'JPEG')
    img_io.seek(0)
    
    # Crear foto
    FotoHuerto.objects.create(
        plantacion=plantacion,
        imagen=ContentFile(img_io.getvalue(), name=f'test_{i}.jpg'),
        etiqueta='GENERAL',
        comentario=f'Foto de prueba {i}',
    )

print("✓ 10 fotos de prueba creadas")
```

---

## ✅ Resultado Esperado

Cuando todo funciona correctamente:

```
CREAR
├─ ✓ Formulario carga
├─ ✓ Drag & Drop funciona
├─ ✓ Preview muestra imagen
├─ ✓ Guardar crea foto
└─ ✓ Redirige a plantación

LEER
├─ ✓ Galería general muestra fotos
├─ ✓ Timeline ordena por fecha
├─ ✓ Detalle amplia imagen
├─ ✓ Navegación funciona
└─ ✓ Filtros aplican

ACTUALIZAR
├─ ✓ Formulario pre-carga datos
├─ ✓ Cambios se guardan
├─ ✓ Imagen puede reemplazarse
└─ ✓ Redirige a detalle

ELIMINAR
├─ ✓ Confirmación aparece
├─ ✓ Archivo se borra
├─ ✓ BD se actualiza
└─ ✓ Redirige a plantación
```

---

## 🎉 Conclusión

Si pasas todos estos checks, ¡el CRUD está **100% funcional** y listo para usar en producción! 🚀

**Documentación de Referencia:**
- [CRUD_FOTOS_README.md](CRUD_FOTOS_README.md) - Guía técnica
- [CRUD_RESUMEN.md](CRUD_RESUMEN.md) - Resumen ejecutivo
- [GALERIA_README.md](GALERIA_README.md) - Sistema completo
