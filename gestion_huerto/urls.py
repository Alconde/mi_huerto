from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('cultivos/', views.lista_cultivos, name='lista_cultivos'),
    path('cultivos/nuevo/', views.editar_cultivo, name='nuevo_cultivo'),
    path('cultivos/<int:cultivo_id>/editar/', views.editar_cultivo, name='editar_cultivo'),
    path('cultivos/<int:cultivo_id>/eliminar/', views.eliminar_cultivo, name='eliminar_cultivo'),
    path('cultivos/<int:cultivo_id>/', views.detalle_cultivo, name='detalle_cultivo'),

    path('variedades/', views.lista_variedades, name='lista_variedades'),
    path('variedades/nueva/', views.editar_variedad, name='nueva_variedad'),
    path('variedades/<int:variedad_id>/editar/', views.editar_variedad, name='editar_variedad'),
    path('variedades/<int:variedad_id>/eliminar/', views.eliminar_variedad, name='eliminar_variedad'),

    path('parcelas/', views.lista_parcelas, name='lista_parcelas'),
    path('parcelas/nueva/', views.editar_parcela, name='nueva_parcela'),
    path('parcelas/<int:parcela_id>/editar/', views.editar_parcela, name='editar_parcela'),
    path('parcelas/<int:parcela_id>/eliminar/', views.eliminar_parcela, name='eliminar_parcela'),
    path('parcelas/<int:parcela_id>/', views.detalle_parcela, name='detalle_parcela'),

    path('plantaciones/', views.lista_plantaciones, name='lista_plantaciones'),
    path('plantaciones/nueva/', views.editar_plantacion, name='nueva_plantacion'),
    path('plantaciones/nueva-mapa/<int:parcela_id>/<int:fila>/<int:columna>/', views.nueva_plantacion_mapa, name='nueva_plantacion_mapa'),
    path('plantaciones/<int:plantacion_id>/editar/', views.editar_plantacion, name='editar_plantacion'),
    path('plantaciones/<int:plantacion_id>/archivar/', views.archivar_plantacion, name='archivar_plantacion'),
    path('plantaciones/<int:plantacion_id>/eliminar/', views.eliminar_plantacion, name='eliminar_plantacion'),
    path('plantaciones/<int:plantacion_id>/', views.detalle_plantacion, name='detalle_plantacion'),    
    path('plantaciones/<int:plantacion_id>/fotos/nueva/', views.agregar_foto_plantacion, name='agregar_foto_plantacion'),
    path('plantaciones/<int:plantacion_id>/cosechas/nueva/', views.agregar_cosecha, name='agregar_cosecha'),

    path('tareas/', views.lista_tareas, name='lista_tareas'),
    path('tareas/nueva/', views.nueva_tarea, name='nueva_tarea'),
    path('tareas/<int:tarea_id>/editar/', views.editar_tarea, name='editar_tarea'),
    path('tareas/<int:tarea_id>/eliminar/', views.eliminar_tarea, name='eliminar_tarea'),
    path('tareas/<int:tarea_id>/', views.detalle_tarea, name='detalle_tarea'),
    path('registrar_riego_rapido/', views.registrar_riego_rapido, name='registrar_riego_rapido'),

    path('botica/', views.lista_botica, name='lista_botica'),
    path('botica/nuevo/', views.crear_remedio_botica, name='crear_remedio_botica'),
    path('botica/<int:pk>/', views.detalle_remedio_botica, name='detalle_remedio_botica'),
    path('botica/<int:pk>/editar/', views.editar_remedio_botica, name='editar_remedio_botica'),
    path('botica/<int:remedio_pk>/aplicaciones/nueva/', views.crear_aplicacion_remedio, name='crear_aplicacion_remedio'),
    path('botica/aplicaciones/<int:pk>/editar/', views.editar_aplicacion_remedio, name='editar_aplicacion_remedio'),

    path('gastos/', views.lista_gastos, name='lista_gastos'),
    path('gastos/nuevo/', views.editar_gasto, name='nuevo_gasto'),
    path('gastos/<int:gasto_id>/editar/', views.editar_gasto, name='editar_gasto'),
    path('gastos/<int:gasto_id>/eliminar/', views.eliminar_gasto, name='eliminar_gasto'),

    path('fotos/', views.galeria_general, name='galeria_general'),
    path('fotos/subir/seleccionar/', views.subir_foto_seleccionar, name='subir_foto_seleccionar'),
    path('fotos/subir/<int:plantacion_id>/', views.subir_foto, name='subir_foto'),
    path('fotos/subir/', views.subir_foto, name='subir_foto'),
    path('fotos/plantacion/<int:plantacion_id>/', views.galeria_plantacion, name='galeria_plantacion'),
    path('fotos/<int:foto_id>/editar/', views.editar_foto, name='editar_foto'),
    path('fotos/<int:foto_id>/eliminar/', views.eliminar_foto, name='eliminar_foto'),
    path('fotos/<int:foto_id>/', views.detalle_foto, name='detalle_foto'),

    path('cosechas/', views.lista_cosechas, name='lista_cosechas'),
    path('cosechas/<int:cosecha_id>/editar/', views.editar_cosecha, name='editar_cosecha'),
    path('cosechas/<int:cosecha_id>/eliminar/', views.eliminar_cosecha, name='eliminar_cosecha'),
    path('cosechas/', views.lista_cosechas, name='lista_cosechas'),
    
    

    path('analisis/', views.analisis_economico, name='analisis_economico'),
    path('calendario/', views.calendario, name='calendario'),
    path('plano/', views.plano_huerto, name='plano_huerto'),
    path('rotaciones/', views.plan_rotaciones, name='plan_rotaciones'),
    path('rotaciones/parcelas/', views.rotaciones_parcelas, name='rotaciones_parcelas'),
]