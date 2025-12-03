from django.contrib import admin
from chamados.models import Chamado 

@admin.register(Chamado)
class ChamadoAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'status', 'prioridade', 'categoria')
    list_filter = ('status', 'prioridade')
    search_fields = ('titulo', 'descricao')