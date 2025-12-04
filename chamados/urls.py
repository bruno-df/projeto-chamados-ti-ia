from django.urls import path
from . import views

urlpatterns = [
    # Rotas Cliente
    path('', views.meus_chamados, name='meus_chamados'),
    path('chamado/<int:id>/', views.detalhe_chamado, name='detalhe_chamado'),
    
    # Rotas Técnico
    path('tecnico/', views.painel_tecnico, name='painel_tecnico'),
    path('tecnico/atender/<int:id>/', views.atender_chamado, name='atender_chamado'),
    path('tecnico/excluir/<int:id>/', views.excluir_chamado, name='excluir_chamado'),
    path('chat/', views.chat_view, name='chat_view'),  # tela do chat
    path('api/chat-mensagem/', views.processar_mensagem, name='processar_mensagem'), # O "correio" das mensagens
]