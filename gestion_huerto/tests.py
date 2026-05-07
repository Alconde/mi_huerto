import string

from django import forms

from django.db.models import Q

from .models import Plantacion, Cultivo, Gasto, Tarea, FotoHuerto, Variedad, Cosecha

from django.core.exceptions import ValidationError





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

COLUMNA_CHOICES = [(i, letra) for i, letra in enumerate(string.ascii_uppercase[:12])]



class PlantacionForm(forms.ModelForm):

    # Cambiamos el campo numérico por un desplegable de letras

    columna_inicio = forms.ChoiceField(choices=COLUMNA_CHOICES, label="Columna Inicio")

    columna_fin = forms.ChoiceField(choices=COLUMNA_CHOICES, label="Columna Fin")



    # Campo especial para variedad manual

    variedad_texto = forms.CharField(

        required=False,

        label="Variedad específica",

        widget=forms.TextInput(attrs={

            'class': 'form-control',

            'placeholder': 'Ej: Cherry, Corazón de Buey, Marmande'

        }),

        help_text="Escribe la variedad específica si no está en la lista"

    )



    variedad = forms.ModelChoiceField(

        queryset=Variedad.objects.none(),

        required=False,

        empty_label="Seleccionar variedad (opcional)",

        help_text="Variedad específica con notas sobre origen y características únicas"

    )



    class Meta:

        model = Plantacion

        exclude = []

        widgets = {

            'cultivo': forms.Select(attrs={'class': 'form-control'}),

            'parcela': forms.Select(attrs={'class': 'form-control'}),

            'variedad': forms.Select(attrs={'class': 'form-control'}),

            'tipo_siembra': forms.RadioSelect(attrs={'class': 'form-check-input'}),

            'fecha_plantacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'fecha_cosecha_estimada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),

            'procedencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Semillero propio, compra local'}),

            'distancia_personalizada': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Opcional: 0 = usar distancia del cultivo'}),

            'fila_inicio': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),

            'fila_fin': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),

            'fecha_cosecha_real': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'cantidad_cosechada': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),

            'unidad_cosecha': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'kg, unidades, cajas, etc.'}),

            'precio_unitario_cosecha': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),

        }



    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        # Para nuevas plantaciones, permitir todas las variedades inicialmente

        # El JavaScript se encargará de filtrar dinámicamente

        self.fields['variedad'].queryset = Variedad.objects.all()



    def clean(self):

        cleaned_data = super().clean()

        cultivo = cleaned_data.get('cultivo')

        variedad = cleaned_data.get('variedad')

        variedad_texto = cleaned_data.get('variedad_texto', '').strip()



        if variedad_texto:

            if not cultivo:

                raise forms.ValidationError("Selecciona primero el cultivo antes de indicar la variedad.")



            variedad_obj, created = Variedad.objects.get_or_create(

                cultivo=cultivo,

                nombre__iexact=variedad_texto,

                defaults={'nombre': variedad_texto}

            )

            cleaned_data['variedad'] = variedad_obj

        elif cultivo and variedad and variedad.cultivo != cultivo:

            raise forms.ValidationError("La variedad seleccionada no pertenece al cultivo elegido.")



        parcela = cleaned_data.get('parcela')

        f_ini = cleaned_data.get('fila_inicio')

        c_ini = int(cleaned_data.get('columna_inicio'))



        if not parcela or f_ini is None:

            return cleaned_data



        # LÓGICA DE VALIDACIÓN GEOMÉTRICA (La misma que el plano)

        # Ajustamos a índice 0 para el cálculo (si el usuario mete 1, restamos 1)

        f = f_ini - 1

        c = c_ini

        error_msg = f"No puedes plantar en la Fila {f_ini}, Columna {string.ascii_uppercase[c]}. Esa zona no tiene tierra según la forma de la {parcela.nombre}."



        if parcela.tipo_tabla == 2:

            ancho_fila = 6 + (f * (6 / 11))

            if c >= ancho_fila:

                raise forms.ValidationError(error_msg)



        elif parcela.tipo_tabla == 3:

            # En la Tabla 3, la diagonal norte: f >= 6 - (c * 0.66)

            altura_minima = 6 - (c * (6 / 9))

            if f < altura_minima:

                raise forms.ValidationError(error_msg)



        return cleaned_data





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

        fields = '__all__'

        widgets = {

            # INFORMACIÓN BÁSICA

            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Tomate'}),

            'familia': forms.Select(attrs={'class': 'form-control'}),

            'emoji': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 🍅'}),

            'requiere_trasplante': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'clasificacion_rotacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Solanácea'}),

            

            # TEMPORADAS

            'epoca_siembra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Primavera-Verano'}),

            

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

        }





class GastoForm(forms.ModelForm):

    class Meta:

        model = Gasto

        fields = '__all__'

        widgets = {

            'fecha_compra': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),

            'concepto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Semillas de tomate'}),

            'categoria': forms.Select(attrs={'class': 'form-control'}),

            'costo': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),

            'lugar_compra': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Agrotop, online, mercado'}),

            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1', 'min': '1'}),

            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas adicionales...'}),

            'ticket_foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),

        }





class TareaForm(forms.ModelForm):

    class Meta:

        model = Tarea

        fields = ['tipo', 'fecha', 'fecha_proxima', 'plantacion', 'zona', 'descripcion', 'estado_suelo']

        widgets = {

            'tipo': forms.Select(attrs={'class': 'form-control'}),

            'fecha': forms.DateInput(

                attrs={'class': 'form-control', 'type': 'date'},

                format='%Y-%m-%d'

            ),

            'fecha_proxima': forms.DateInput(

                attrs={'class': 'form-control', 'type': 'date'},

                format='%Y-%m-%d'

            ),

            'plantacion': forms.Select(attrs={'class': 'form-control'}),

            'zona': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: T1, T2, T3, Tabla 1, Sector Norte'}),

            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Notas sobre la tarea realizada...'}),

            'estado_suelo': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Estado del suelo: humedad, textura, etc.'}),

        }





class FotoHuertoForm(forms.ModelForm):

    """Formulario para subir y gestionar fotos del huerto"""

    class Meta:

        model = FotoHuerto

        fields = ['imagen', 'etiqueta', 'descripcion', 'plantacion']

        widgets = {

            'imagen': forms.ClearableFileInput(attrs={

                'class': 'form-control',

                'accept': 'image/*',

                'style': 'display: none;'

            }),

            'etiqueta': forms.Select(attrs={

                'class': 'form-control'

            }),

            'descripcion': forms.Textarea(attrs={

                'class': 'form-control',

                'rows': 4,

                'placeholder': 'Notas sobre lo que ves en la foto...'

            }),

            'plantacion': forms.Select(attrs={

                'class': 'form-control'

            }),

        }





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