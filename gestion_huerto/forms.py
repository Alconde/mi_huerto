import string
import math
from django import forms
from django.db.models import Q
from .models import (Plantacion, Cultivo, Gasto, Tarea, FotoHuerto, Variedad, 
                     Cosecha, FotoPlantacion, Parcela, HistorialRotacion, RotacionParcela, 
                     FichaFrutal, FichaFlor, RemedioBotica, AplicacionRemedio, Cosecha)
from django.core.exceptions import ValidationError

from .models import RemedioBotica
from django.db import models






def validar_meses(valor):
    """Valida que el valor sea meses válidos (1-12) separados por comas"""
    if not valor:
        return
    
    try:
        meses = [int(m.strip()) for m in valor.split(',')]
    except ValueError:
        raise ValidationError("Debes ingresar solo números separados por comas")
    
    for mes in meses:
        if mes < 1 or mes > 12:
            raise ValidationError(f"El mes {mes} es inválido. Los meses deben estar entre 1-12")
    
    if len(meses) != len(set(meses)):
        raise ValidationError("No puedes repetir el mismo mes")


# Generamos las opciones de letras (A=0, B=1, C=2...)







COLUMNA_CHOICES = [(str(i), str(i)) for i in range(20)]


class PlantacionForm(forms.ModelForm):
    columna_inicio = forms.ChoiceField(
        choices=COLUMNA_CHOICES,
        label="Columna inicio",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    columna_fin = forms.ChoiceField(
        choices=COLUMNA_CHOICES,
        label="Columna fin",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    variedad_texto = forms.CharField(
        required=False,
        label="Variedad específica",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Cherry, Corazón de buey, Marmande',
            'autocomplete': 'off',
        }),
    )

    class Meta:
        model = Plantacion
        fields = [
            'cultivo',
            'parcela',
            'variedad',            
            'estado',
            'fecha_siembra',
            'fecha_germinado_estimado',
            'fecha_germinado_real',
            'fecha_trasplante',
            'modo_implantacion',
            'fecha_recoleccion_inicio',
            'procedencia',
            'origen_plantel',
            'distancia_personalizada',
            'cantidad',
            'fila_inicio',
            'fila_fin',
            'precio_unitario_cosecha',
            'observaciones_seguimiento',
            'notas',
        ]
        widgets = {
            'cultivo': forms.Select(attrs={'class': 'form-select'}),
            'parcela': forms.Select(attrs={'class': 'form-select'}),
            'variedad': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'procedencia': forms.Select(attrs={'class': 'form-select'}),

            'fecha_siembra': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'fecha_germinado_estimado': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'fecha_germinado_real': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'fecha_trasplante': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'modo_implantacion': forms.RadioSelect(), 

            'fecha_recoleccion_inicio': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),

            'distancia_personalizada': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Distancia en cm (opcional)',
                'step': '0.01',
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Nº de plantas',
            }),
            'fila_inicio': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
            'fila_fin': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
            'precio_unitario_cosecha': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'origen_plantel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: semillero propio, vivero local...'
            }),
            'observaciones_seguimiento': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Estado general del cultivo, incidencias, vigor, etc.'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre la plantación',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['variedad'].required = False
        self.fields['variedad'].queryset = Variedad.objects.all()

        self.fields['fecha_siembra'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_germinado_estimado'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_germinado_real'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_trasplante'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_recoleccion_inicio'].input_formats = ['%Y-%m-%d']

        instance = self.instance if self.instance and self.instance.pk else None

        if instance and not self.data:
            self.initial['columna_inicio'] = str(instance.columna_inicio)
            self.initial['columna_fin'] = str(instance.columna_fin)

            if instance.variedad:
                self.initial['variedad_texto'] = instance.variedad.nombre

        elif not instance:
            self.initial['fila_inicio'] = 1
            self.initial['fila_fin'] = 1
            self.initial['columna_inicio'] = '0'
            self.initial['columna_fin'] = '0'

    def clean_variedad_texto(self):
        return (self.cleaned_data.get('variedad_texto') or '').strip()

    def clean(self):
        cleaned_data = super().clean()

        cultivo = cleaned_data.get('cultivo')
        variedad = cleaned_data.get('variedad')
        variedad_texto = cleaned_data.get('variedad_texto')

        parcela = cleaned_data.get('parcela')
        fila_inicio = cleaned_data.get('fila_inicio')
        fila_fin = cleaned_data.get('fila_fin')
        columna_inicio = cleaned_data.get('columna_inicio')
        columna_fin = cleaned_data.get('columna_fin')
        
        modo_implantacion = cleaned_data.get('modo_implantacion')
        fecha_trasplante = cleaned_data.get('fecha_trasplante')

        if variedad_texto:
            if not cultivo:
                self.add_error(
                    'cultivo',
                    'Selecciona primero el cultivo antes de indicar la variedad.'
                )
            else:
                variedad_obj = Variedad.objects.filter(
                    cultivo=cultivo,
                    nombre__iexact=variedad_texto
                ).first()

                if not variedad_obj:
                    variedad_obj = Variedad.objects.create(
                        cultivo=cultivo,
                        nombre=variedad_texto
                    )

                cleaned_data['variedad'] = variedad_obj

        elif cultivo and variedad and variedad.cultivo != cultivo:
            self.add_error(
                'variedad',
                'La variedad seleccionada no pertenece al cultivo elegido.'
            )

        if fila_inicio is not None and fila_fin is not None and fila_inicio > fila_fin:
            self.add_error(
                'fila_fin',
                'La fila final no puede ser menor que la fila inicial.'
            )

        if columna_inicio is not None and columna_fin is not None:
            c_ini = int(columna_inicio)
            c_fin = int(columna_fin)

            if c_ini > c_fin:
                self.add_error(
                    'columna_fin',
                    'La columna final no puede ser menor que la columna inicial.'
                )

        if parcela:
            if fila_inicio is not None and hasattr(parcela, 'filas') and fila_inicio > parcela.filas:
                self.add_error(
                    'fila_inicio',
                    f'La parcela {parcela.nombre} tiene {parcela.filas} filas.'
                )

            if fila_fin is not None and hasattr(parcela, 'filas') and fila_fin > parcela.filas:
                self.add_error(
                    'fila_fin',
                    f'La parcela {parcela.nombre} tiene {parcela.filas} filas.'
                )

            if columna_inicio is not None and hasattr(parcela, 'columnas') and int(columna_inicio) >= parcela.columnas:
                self.add_error(
                    'columna_inicio',
                    f'La parcela {parcela.nombre} tiene {parcela.columnas} columnas.'
                )

            if columna_fin is not None and hasattr(parcela, 'columnas') and int(columna_fin) >= parcela.columnas:
                self.add_error(
                    'columna_fin',
                    f'La parcela {parcela.nombre} tiene {parcela.columnas} columnas.'
                )

        # Validaciones adaptadas a modo_implantacion en lugar de tipo_siembra
        if modo_implantacion == 'semillero' and not fecha_trasplante:
            # Opcional: podrías avisar o validar que semillero debería tener trasplante
            pass

        if modo_implantacion == 'directa' and fecha_trasplante:
            self.add_error(
                'fecha_trasplante',
                'Si la entrada es siembra directa, normalmente no debe registrarse trasplante.'
            )

        return cleaned_data

    def save(self, commit=True):
        plantacion = super().save(commit=False)

        plantacion.variedad = self.cleaned_data.get('variedad')
        plantacion.columna_inicio = int(self.cleaned_data.get('columna_inicio') or 0)
        plantacion.columna_fin = int(self.cleaned_data.get('columna_fin') or 0)

        if hasattr(plantacion, 'fecha_recoleccion_esperada'):
            plantacion.fecha_recoleccion_esperada = self.cleaned_data.get('fecha_recoleccion_inicio')

        if commit:
            plantacion.save()
            self.save_m2m()

        return plantacion
    
class CultivoForm(forms.ModelForm):
    # Campos de meses con validación
    meses_siembra = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 1,2,3 (enero, febrero, marzo)',
            'data-help': 'Números 1-12 separados por comas'
        }),
        validators=[validar_meses],
        help_text="Números 1-12 separados por comas (1=Enero, 12=Diciembre)"
    )
    
    meses_trasplante = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 4,5',
            'data-help': 'Números 1-12 separados por comas'
        }),
        validators=[validar_meses],
        help_text="Números 1-12 separados por comas"
    )

    meses_recoleccion = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 7,8,9,10',
            'data-help': 'Números 1-12 separados por comas'
        }),
        validators=[validar_meses],
        help_text="Números 1-12 separados por comas"
    )

    class Meta:
        model = Cultivo
        # Incluimos explícitamente todos los campos (incluyendo tipo_cultivo y es_perenne)
        fields = '__all__'
        widgets = {
            # TIPO Y PROPIEDADES GENERALES
            'tipo_cultivo': forms.Select(attrs={'class': 'form-control'}),
            'es_perenne': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            # INFORMACIÓN BÁSICA
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tomate'}),
            'familia': forms.Select(attrs={'class': 'form-control'}),
            'emoji': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 🍅'}),
            'requiere_trasplante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'clasificacion_rotacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Solanácea'}),
            'grupo_rotacion': forms.Select(attrs={'class': 'form-control'}),

            # TEMPORADAS
            'epoca_siembra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Primavera-Verano'}),
            'epoca_trasplante': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Primavera'}),
            'epoca_recoleccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Verano-Otoño'}),

            # DATOS TÉCNICOS
            'marco_plantacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 40x40 cm'}),
            'distancia_plantas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '40 (cm)'}),
            'distancia_lineas': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '40 (cm)'}),
            'profundidad_siembra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 2-3 cm'}),

            # GERMINACIÓN
            'temp_min_germinacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '°C'}),
            'temp_optima_germinacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '°C'}),
            'temp_max_germinacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '°C'}),
            'tiempo_germinacion': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Días'}),

            # CICLO
            'dias_ciclo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 70 días'}),

            # CUIDADOS DEL CULTIVO
            'riego': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Frecuencia y método recomendado'}),
            'abono': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Tipo y frecuencia de fertilización'}),
            'mantenimiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Poda, tutorado, etc.'}),
            'plagas_comunes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'enfermedades_comunes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notas_locales': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_cultivo = cleaned_data.get('tipo_cultivo')
        grupo_rotacion = cleaned_data.get('grupo_rotacion')

        # Frutal normalmente perenne: forzamos es_perenne=True como ayuda
        if tipo_cultivo == 'frutal':
            cleaned_data['es_perenne'] = True

        # Aviso suave si intentas usar grupo de rotación con frutales/flores
        if tipo_cultivo in ['frutal', 'flor'] and grupo_rotacion:
            self.add_error(
                'grupo_rotacion',
                'En general frutales y flores no se incluyen en la rotación clásica de hortalizas.'
            )

        return cleaned_data

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = [
            'fecha_compra',
            'concepto',
            'categoria',
            'coste',
            'cantidad',
            'lugar_compra',
            'notas',
            'ticket_foto',
        ]
        widgets = {
            'fecha_compra': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'concepto': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Semillas de tomate RAF'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'coste': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1',
                'min': '1'
            }),
            'lugar_compra': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Agrotop, Leroy Merlin, Mercado local'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas adicionales sobre la compra...'
            }),
            'ticket_foto': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'fecha_compra': 'Fecha de compra',
            'concepto': 'Concepto',
            'categoria': 'Categoría',
            'coste': 'Precio unitario (€)',
            'cantidad': 'Cantidad',
            'lugar_compra': 'Lugar de compra',
            'notas': 'Notas',
            'ticket_foto': 'Foto del ticket',
        }


class TareaForm(forms.ModelForm):
    class Meta:
        model = Tarea
        fields = [
            'tipo', 'fecha', 'fecha_proxima',
            'todo_el_huerto', 'plantaciones',
            'zona', 'descripcion', 'estado_suelo', 'completada',
            'tiempo_estimado_min', 'tiempo_real_min',
        ]
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'fecha_proxima': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'todo_el_huerto': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'plantaciones': forms.CheckboxSelectMultiple(),
            'zona': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: T1, T2, T3, Tabla 1, Sector Norte'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas sobre la tarea realizada...'
            }),
            'estado_suelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estado del suelo: humedad, textura, etc.'
            }),
            'completada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tiempo_estimado_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Ej: 30'
            }),
            'tiempo_real_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Ej: 45'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha'].input_formats = ['%Y-%m-%d']
        self.fields['fecha_proxima'].input_formats = ['%Y-%m-%d']
        self.fields['plantaciones'].required = False

        self.fields['plantaciones'].queryset = (
            Plantacion.objects.select_related('cultivo', 'parcela')
            .order_by('cultivo__nombre', 'parcela__nombre')
        )
        self.fields['plantaciones'].queryset = Plantacion.objects.exclude(
            estado__in=['finalizada', 'perdida']
        ).select_related('cultivo', 'variedad', 'parcela').order_by(
            'parcela__nombre', 'cultivo__nombre', 'variedad__nombre'
        )

        self.fields['plantaciones'].label_from_instance = lambda p: (
            f"{p.cultivo.emoji} {p.cultivo.nombre}"
            f"{' (' + p.variedad.nombre + ')' if p.variedad else ''}"
            f" — {p.parcela.nombre}"
            f" F{p.fila_inicio}-{p.fila_fin}"
        )

        self.fields['tiempo_estimado_min'].required = False
        self.fields['tiempo_real_min'].required = False
        self.fields['tiempo_estimado_min'].label = 'Tiempo estimado (min)'
        self.fields['tiempo_real_min'].label = 'Tiempo real (min)'
        self.fields['tiempo_estimado_min'].help_text = 'Duración prevista en minutos.'
        self.fields['tiempo_real_min'].help_text = 'Duración real empleada en minutos.'

    def clean(self):
        cleaned_data = super().clean()
        todo_el_huerto = cleaned_data.get('todo_el_huerto')
        plantaciones = cleaned_data.get('plantaciones')
        tiempo_estimado_min = cleaned_data.get('tiempo_estimado_min')
        tiempo_real_min = cleaned_data.get('tiempo_real_min')

        if todo_el_huerto:
            cleaned_data['plantaciones'] = Plantacion.objects.none()

        if not todo_el_huerto and not plantaciones and not cleaned_data.get('zona'):
            pass

        if tiempo_estimado_min is not None and tiempo_estimado_min <= 0:
            self.add_error('tiempo_estimado_min', 'Introduce un número de minutos mayor que 0.')

        if tiempo_real_min is not None and tiempo_real_min <= 0:
            self.add_error('tiempo_real_min', 'Introduce un número de minutos mayor que 0.')

        return cleaned_data
    
class FotoHuertoForm(forms.ModelForm):
    """Formulario para subir y gestionar fotos del huerto"""
    class Meta:
        model = FotoHuerto
        fields = ['imagen', 'fecha_foto', 'etiqueta', 'comentario', 'es_hito', 'tipo_hito']
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'style': 'display: none;'
            }),
            'fecha_foto': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'etiqueta': forms.Select(attrs={
                'class': 'form-control'
            }),
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Notas sobre lo que ves en la foto...'
            }),
            'es_hito': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tipo_hito': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Primera Flor, Primer Fruto, Plaga Detectada'
            }),
        }



class FotoPlantacionForm(forms.ModelForm):
    """
    Formulario para agregar fotos al histórico de una plantación
    a lo largo de su ciclo de vida.
    """

    class Meta:
        model = FotoPlantacion
        fields = ['imagen', 'fecha_foto', 'tipo_foto', 'dias_ciclo', 'descripcion']
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'fecha_foto': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'tipo_foto': forms.Select(attrs={
                'class': 'form-select',
            }),
            'dias_ciclo': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Se calcula automáticamente si está vacío',
                'min': '1',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe el estado de la plantación, cambios observados, plagas, vigor, floración, etc.',
            }),
        }
        labels = {
            'imagen': 'Imagen',
            'fecha_foto': 'Fecha de la foto',
            'tipo_foto': 'Etapa del cultivo',
            'dias_ciclo': 'Días de ciclo',
            'descripcion': 'Descripción',
        }
        help_texts = {
            'imagen': 'Sube una foto del estado actual de la plantación.',
            'fecha_foto': 'Fecha en la que se tomó la foto.',
            'tipo_foto': 'Selecciona la etapa del cultivo en ese momento.',
            'dias_ciclo': 'Si lo dejas vacío, se calculará automáticamente desde la fecha de siembra.',
            'descripcion': 'Añade observaciones útiles: crecimiento, color, plagas, síntomas, floración o hitos importantes.',
        }

    def clean_dias_ciclo(self):
        dias_ciclo = self.cleaned_data.get('dias_ciclo')
        if dias_ciclo is not None and dias_ciclo < 1:
            raise forms.ValidationError('Los días de ciclo deben ser mayores que 0.')
        return dias_ciclo

class CosechaForm(forms.ModelForm):

    class Meta:

        model = Cosecha

        fields = ['fecha_cosecha', 'cantidad', 'unidad', 'precio_unitario', 'notas']

        widgets = {

            'fecha_cosecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),

            'unidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kg'}),

            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),

            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas sobre la cosecha...'}),

        }

        
class HistorialRotacionForm(forms.ModelForm):
    class Meta:
        model = HistorialRotacion
        fields = ['parcela', 'cultivo_anterior', 'cultivo_siguiente', 'fecha_rotacion', 'observaciones']
        widgets = {
            'fecha_rotacion': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        parcela = cleaned_data.get('parcela')
        cultivo_siguiente = cleaned_data.get('cultivo_siguiente')
        cultivo_anterior = cleaned_data.get('cultivo_anterior')

        if cultivo_anterior and cultivo_siguiente:
            if cultivo_anterior.familia == cultivo_siguiente.familia:
                raise ValidationError("No conviene rotar a un cultivo de la misma familia botánica.")

        if parcela and cultivo_siguiente:
            ultimas = parcela.historial_rotaciones.select_related('cultivo_siguiente').order_by('-fecha_rotacion')[:3]
            familias_recientes = [
                r.cultivo_siguiente.familia
                for r in ultimas
                if r.cultivo_siguiente
            ]

            if cultivo_siguiente.familia in familias_recientes:
                raise ValidationError(
                    "Esta familia ya aparece recientemente en esta parcela. "
                    "Intenta esperar 3-4 años antes de repetirla."
                )

        return cleaned_data
    

class RotacionParcelaForm(forms.ModelForm):
    class Meta:
        model = RotacionParcela
        fields = ['parcela', 'cultivo', 'fecha_inicio', 'fecha_fin', 'temporada', 'notas']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'temporada': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Primavera 2026'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parcela': forms.Select(attrs={'class': 'form-select'}),
            'cultivo': forms.Select(attrs={'class': 'form-select'}),
        }

class FichaFrutalForm(forms.ModelForm):
    class Meta:
        model = FichaFrutal
        fields = [
            'variedad_frutal',
            'portainjerto',
            'tipo_polinizacion',
            'necesita_polinizador',
            'marco_plantacion_m',
            'tipo_poda',
            'fecha_ultima_poda',
            'observaciones',
        ]
        widgets = {
            'fecha_ultima_poda': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'variedad_frutal': forms.TextInput(attrs={'class': 'form-control'}),
            'portainjerto': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_polinizacion': forms.Select(attrs={'class': 'form-select'}),
            'tipo_poda': forms.Select(attrs={'class': 'form-select'}),
            'marco_plantacion_m': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }

class FichaFlorForm(forms.ModelForm):
    class Meta:
        model = FichaFlor
        fields = [
            'funcion_ecologica',
            'floracion_inicio_mes',
            'floracion_fin_mes',
            'atrae_polinizadores',
            'observaciones',
        ]
        widgets = {
            'funcion_ecologica': forms.Select(attrs={'class': 'form-select'}),
            'floracion_inicio_mes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'floracion_fin_mes': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 12}),
            'atrae_polinizadores': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('floracion_inicio_mes')
        fin = cleaned_data.get('floracion_fin_mes')

        if inicio and (inicio < 1 or inicio > 12):
            self.add_error('floracion_inicio_mes', 'El mes debe estar entre 1 y 12.')

        if fin and (fin < 1 or fin > 12):
            self.add_error('floracion_fin_mes', 'El mes debe estar entre 1 y 12.')

        if inicio and fin and fin < inicio:
            self.add_error('floracion_fin_mes', 'El mes de fin no puede ser anterior al de inicio.')

        return cleaned_data
    
class RemedioBoticaForm(forms.ModelForm):
    class Meta:
        model = RemedioBotica
        fields = [
            'nombre',
            'tipo',
            'objetivo',
            'ingredientes',
            'preparacion',
            'dosis',
            'modo_aplicacion',
            'periodicidad',
            'momento_ideal',
            'advertencias',
            'activo',
            'notas',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Jabón potásico'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'objetivo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: pulgón, mosca blanca, oídio...'
            }),
            'ingredientes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ingredientes y cantidades base'
            }),
            'preparacion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Explica paso a paso cómo lo preparas'
            }),
            'dosis': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 10 ml/L'
            }),
            'modo_aplicacion': forms.Select(attrs={'class': 'form-select'}),
            'periodicidad': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: cada 7 días'
            }),
            'momento_ideal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: al atardecer, sin lluvia'
            }),
            'advertencias': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Precauciones y malas prácticas a evitar'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones personales'
            }),
        }

class AplicacionRemedioForm(forms.ModelForm):
    crear_seguimiento = forms.BooleanField(
        required=False,
        label='Crear tarea de seguimiento',
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    dias_hasta_seguimiento = forms.IntegerField(
        required=False,
        min_value=1,
        initial=7,
        label='Días hasta el seguimiento',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'placeholder': 'Ej: 7'
        }),
        help_text='Indica en cuántos días quieres revisar el efecto del tratamiento.'
    )

    class Meta:
        model = AplicacionRemedio
        fields = [
            'fecha_aplicacion',
            'cultivo',
            'parcela',
            'problema_detectado',
            'dosis_aplicada',
            'condiciones',
            'resultado',
            'repetir',
            'observaciones',
        ]
        widgets = {
            'fecha_aplicacion': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
                format='%Y-%m-%d'
            ),
            'cultivo': forms.Select(attrs={'class': 'form-select'}),
            'parcela': forms.Select(attrs={'class': 'form-select'}),
            'problema_detectado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: pulgón, oídio, prevención...'
            }),
            'dosis_aplicada': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 10 ml/L'
            }),
            'condiciones': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: tarde seca, sin viento'
            }),
            'resultado': forms.Select(attrs={'class': 'form-select'}),
            'repetir': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Efectos observados, respuesta del cultivo, evolución...'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.remedio = kwargs.pop('remedio', None)
        super().__init__(*args, **kwargs)

        self.fields['fecha_aplicacion'].input_formats = ['%Y-%m-%d']

        if not self.is_bound:
            self.fields['crear_seguimiento'].initial = False
            self.fields['dias_hasta_seguimiento'].initial = 7

    def clean(self):
        cleaned_data = super().clean()

        crear_seguimiento = cleaned_data.get('crear_seguimiento')
        dias_hasta_seguimiento = cleaned_data.get('dias_hasta_seguimiento')

        if crear_seguimiento and not dias_hasta_seguimiento:
            self.add_error(
                'dias_hasta_seguimiento',
                'Indica cuántos días deben pasar hasta el seguimiento.'
            )

        return cleaned_data

class CosechaForm(forms.ModelForm):
    class Meta:
        model = Cosecha
        fields = ['fecha_cosecha', 'cantidad', 'unidad', 'precio_unitario', 'notas']
        widgets = {
            'fecha_cosecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'unidad': forms.Select(attrs={
                'class': 'form-control'
            }),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'notas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notas sobre la cosecha...'
            }),
        }
        labels = {
            'fecha_cosecha': 'Fecha de cosecha',
            'cantidad': 'Cantidad',
            'unidad': 'Unidad',
            'precio_unitario': 'Precio de mercado',
            'notas': 'Notas',
        }