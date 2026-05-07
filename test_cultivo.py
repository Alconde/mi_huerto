import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','huerto_proyecto.settings')
import django
django.setup()

from gestion_huerto.models import Cultivo

print('FAMILIA_LABELS', Cultivo.FAMILIA_LABELS)
print('FAMILIA_COLORS', Cultivo.FAMILIA_COLORS)

c = Cultivo(nombre='Prueba', familia='LEG')
print('familia_label', c.familia_label)
print('familia_color', c.familia_color)