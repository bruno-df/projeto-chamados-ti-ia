import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Chamado
from .ai_service import analisar_chamado # import IA
from .ai_service import analisar_chamado, chat_com_ia
from .ai_service import analisar_chamado, chat_com_ia, extrair_dados_chat

 # cliente views

@login_required
def meus_chamados(request):
    # Mostra apenas os chamados do utilizador logado
    chamados = Chamado.objects.filter(cliente=request.user)
    return render(request, 'cliente/lista_chamados.html', {'chamados': chamados})

@login_required
def detalhe_chamado(request, id):
    # Garante que o cliente só vê os seus próprios chamados
    chamado = get_object_or_404(Chamado, id=id)
    if not request.user.is_staff and chamado.cliente != request.user:
        return redirect('meus_chamados')
        
    return render(request, 'cliente/detalhe_chamado.html', {'chamado': chamado})

# tecnico views

@login_required
def painel_tecnico(request):
    # Verifica se é staff/técnico
    if not request.user.is_staff:
        return redirect('meus_chamados')
    
    # Pega todos os chamados
    chamados = Chamado.objects.all()
    return render(request, 'tecnico/painel.html', {'chamados': chamados})

def excluir_chamado(request, id):
    # Segurança: Só técnicos podem excluir
    if not request.user.is_staff:
        return redirect('meus_chamados')
    
    # Busca o chamado
    chamado = get_object_or_404(Chamado, id=id)
    
    # Deleta do banco de dados
    chamado.delete()
    
    # Volta para o painel
    return redirect('painel_tecnico')

@login_required
    # tecnico atende o chamado e troca o status dele, se encerrar o chamado, salva a solução e data de fechamento
def atender_chamado(request, id):
    if not request.user.is_staff:
        return redirect('meus_chamados')
        
    chamado = get_object_or_404(Chamado, id=id)
    
    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        if acao == 'assumir':
            chamado.status = 'EM_ATENDIMENTO'
            chamado.tecnico = request.user
            chamado.save()
            
        elif acao == 'encerrar':
            solucao = request.POST.get('solucao')
            chamado.status = 'ENCERRADO'
            chamado.solucao_tecnico = solucao
            chamado.data_fechamento = timezone.now()
            chamado.save()
            return redirect('painel_tecnico')
            
    return render(request, 'tecnico/atender_chamado.html', {'chamado': chamado})

def chat_view(request):
    # Limpa o histórico ao entrar na página para começar conversa nova
    request.session['historico_chat'] = []
    return render(request, 'cliente/chat.html')

@csrf_exempt
def processar_mensagem(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            mensagem_usuario = dados.get('mensagem')
            
            # Recupera histórico
            historico = request.session.get('historico_chat', [])
            historico.append(f"Usuário: {mensagem_usuario}")
            
            # Pergunta à IA o que responder
            resposta_ia = chat_com_ia(historico)
            
            if "FIM_DA_ENTREVISTA" in resposta_ia:
                # IA decidiu que acabou. Extrai os dados.
                dados_finais = extrair_dados_chat(historico)
                
                # Criar o chamado no Banco de Dados
                novo_chamado = Chamado.objects.create(
                    cliente=request.user,
                    titulo=dados_finais['resumo'],
                    descricao=dados_finais['descricao_completa'],
                    categoria=dados_finais['categoria'],
                    prioridade=dados_finais['prioridade'],
                    sugestao_ia=dados_finais['sugestao_ia'],
                    status='ABERTO' # Chat sempre abre como novo
                )
                
                # Limpa a memória para a próxima vez
                request.session['historico_chat'] = []
                
                # Avisa o usuário com o número do protocolo
                msg_final = f"✅ Tudo certo! As informações foram coletadas. Seu chamado de ID #{novo_chamado.id} foi aberto com sucesso. Título: {novo_chamado.titulo}."
                return JsonResponse({'resposta': msg_final})

            # Se não acabou, continua a conversa normal
            historico.append(f"IA: {resposta_ia}")
            request.session['historico_chat'] = historico
            
            return JsonResponse({'resposta': resposta_ia})
            
        except Exception as e:
            print(f"Erro: {e}")
            return JsonResponse({'erro': 'Erro interno'}, status=400)
            
    return JsonResponse({'erro': 'Método inválido'}, status=400)