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

# --- ÁREA DO CLIENTE ---

@login_required
def meus_chamados(request):
    # Mostra apenas os chamados do utilizador logado
    chamados = Chamado.objects.filter(cliente=request.user)
    return render(request, 'cliente/lista_chamados.html', {'chamados': chamados})

@login_required
def novo_chamado(request):
    # REDIRECIONAMENTO:
    # Se o cliente tentar acessar o formulário manual, enviamos ele para o chat.
    # Isso desativa a criação manual para clientes.
    return redirect('chat_view')

    # --- O CÓDIGO ABAIXO FICA INATIVO (MEMÓRIA) ---
    # (Mantemos aqui comentado caso um dia queiras voltar atrás)
    """
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        analise = analisar_chamado(descricao)
        Chamado.objects.create(
            cliente=request.user,
            titulo=titulo,
            descricao=descricao,
            categoria=analise['categoria'],
            prioridade=analise['prioridade'],
            sugestao_ia=analise['sugestão']
        )
        return redirect('meus_chamados')
    return render(request, 'cliente/novo_chamado.html')
    """

@login_required
def detalhe_chamado(request, id):
    # Garante que o cliente só vê os seus próprios chamados (ou se for técnico)
    chamado = get_object_or_404(Chamado, id=id)
    if not request.user.is_staff and chamado.cliente != request.user:
        return redirect('meus_chamados')
        
    return render(request, 'cliente/detalhe_chamado.html', {'chamado': chamado})

# --- ÁREA DO TÉCNICO ---

@login_required
def painel_tecnico(request):
    # Verifica se é staff/técnico
    if not request.user.is_staff:
        return redirect('meus_chamados')
    
    # Pega todos os chamados
    chamados = Chamado.objects.all()
    return render(request, 'tecnico/painel.html', {'chamados': chamados})

def excluir_chamado(request, id):
    # 1. Segurança: Só técnicos podem excluir
    if not request.user.is_staff:
        return redirect('meus_chamados')
    
    # 2. Busca o chamado
    chamado = get_object_or_404(Chamado, id=id)
    
    # 3. Deleta do banco de dados
    chamado.delete()
    
    # 4. Volta para o painel
    return redirect('painel_tecnico')

@login_required
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
            
            # Resposta temporária (Eco)
            resposta_sistema = f"Recebi: '{mensagem_usuario}'. (Aguardando integração com IA)"
            
            return JsonResponse({'resposta': resposta_sistema})
        except:
             return JsonResponse({'erro': 'Erro ao processar JSON'}, status=400)
        
    return JsonResponse({'erro': 'Método inválido'}, status=400)

@csrf_exempt
def processar_mensagem(request):
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            mensagem_usuario = dados.get('mensagem')
            
            # 1. Recupera o histórico da sessão ou cria uma lista vazia se for a primeira vez
            historico = request.session.get('historico_chat', [])
            
            # 2. Adiciona a fala do usuário ao histórico
            historico.append(f"Usuário: {mensagem_usuario}")
            
            # 3. Chama a IA passando tudo o que já foi dito
            resposta_ia = chat_com_ia(historico)
            
            # 4. Adiciona a resposta da IA ao histórico
            historico.append(f"IA: {resposta_ia}")
            
            # 5. Salva a memória atualizada na sessão
            request.session['historico_chat'] = historico
            
            # (Futuro: Aqui vamos verificar se a IA disse "FIM_DA_ENTREVISTA" para criar o chamado)
            
            return JsonResponse({'resposta': resposta_ia})
            
        except Exception as e:
            print(f"Erro: {e}")
            return JsonResponse({'erro': 'Erro interno'}, status=400)
        
    return JsonResponse({'erro': 'Método inválido'}, status=400)

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
                # 1. IA decidiu que acabou. Extrai os dados.
                dados_finais = extrair_dados_chat(historico)
                
                # 2. Criar o chamado no Banco de Dados
                novo_chamado = Chamado.objects.create(
                    cliente=request.user,
                    titulo=dados_finais['resumo'],
                    descricao=dados_finais['descricao_completa'],
                    categoria=dados_finais['categoria'],
                    prioridade=dados_finais['prioridade'],
                    sugestao_ia=dados_finais['sugestao_ia'],
                    status='ABERTO' # Chat sempre abre como novo
                )
                
                # 3. Limpa a memória para a próxima vez
                request.session['historico_chat'] = []
                
                # 4. Avisa o usuário com o número do protocolo
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