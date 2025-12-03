from django.db import models
from django.contrib.auth.models import User

class Chamado(models.Model):
    # Opções para campos de seleção
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('EM_ATENDIMENTO', 'Em Atendimento'),
        ('ENCERRADO', 'Encerrado'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
    ]
    
    CATEGORIA_CHOICES = [
        ('HARDWARE', 'Hardware'),
        ('SOFTWARE', 'Software'),
        ('REDE', 'Rede'),
        ('OUTRO', 'Outro'),
    ]

    # Dados básicos
    titulo = models.CharField(max_length=100)
    descricao = models.TextField(verbose_name="Descrição do Problema")
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chamados_criados')
    data_abertura = models.DateTimeField(auto_now_add=True)
    
    # Dados gerados pela IA ou Sistema
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTO')
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES, default='OUTRO')
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='BAIXA')
    sugestao_ia = models.TextField(blank=True, null=True, verbose_name="Sugestão da IA")
    
    # Dados do Técnico
    tecnico = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chamados_atendidos')
    solucao_tecnico = models.TextField(blank=True, null=True, verbose_name="Solução Final")
    data_fechamento = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"#{self.id} - {self.titulo} ({self.status})"

    class Meta:
        ordering = ['-prioridade', '-data_abertura'] # Ordena por prioridade (Alta primeiro) e depois data