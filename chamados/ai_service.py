import google.generativeai as genai
import json
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")

genai.configure(api_key=API_KEY)

def analisar_chamado(descricao):
    #Envia a descrição para a API do Gemini e retorna categoria, prioridade e sugestão.
    

    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Prompt com instruções estritas.
    prompt = f"""
    Você é um assistente de suporte técnico experiente (Helpdesk).
    Analise o seguinte problema relatado por um cliente:
    
    "{descricao}"
    
    Sua tarefa é retornar APENAS um objeto JSON (sem markdown, sem aspas extras) com as seguintes chaves:
    1. "categoria": Escolha uma entre: HARDWARE, SOFTWARE, REDE, OUTRO.
    2. "prioridade": Escolha uma entre: BAIXA, MEDIA, ALTA.
    3. "sugestão": Uma solução técnica curta e direta para o usuário tentar (máximo 2 frases).
    
    Responda apenas o JSON.
    """
    
    try:
        # enviamos o pedido para a IA
        response = model.generate_content(prompt)

        # Remove possíveis blocos de código (```json ... ```) que alguns modelos incluem
        texto_resposta = texto_resposta.replace("```json", "").replace("```", "").strip()

        # Converte o texto JSON retornado pela IA em um dict Python,
        # transforma em JSON torna a saída previsível e legível pela máquina,
        # permitindo validação, mapeamento direto para o banco de dados e aplicação de valores padrão se campos estiverem ausentes.
        dados = json.loads(texto_resposta)
        
        return {
            'categoria': dados.get('categoria', 'OUTRO'),
            'prioridade': dados.get('prioridade', 'MEDIA'),
            'sugestão': dados.get('sugestão', 'Sem sugestão automática.')
        }

    except Exception as e:
        print(f"Erro na IA: {e}")
        # Se a IA falhar ou a internet cair, o sistema não para.
        return {
            'categoria': 'OUTRO',
            'prioridade': 'MEDIA',
            'sugestão': 'Não foi possível contatar a IA. Aguarde um técnico.'
        }
    
def chat_com_ia(historico_conversa):
    #Recebe uma lista de mensagens (ex: "IA: Olá...", "User: Meu nome é Nagafe") e gera a próxima resposta da IA.
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Transformamos a lista em um texto único para a IA entender o contexto
    conversa_texto = "\n".join(historico_conversa)
    
    prompt = f"""
    Você é uma atendente de suporte técnico simpática e eficiente.
    Seu objetivo é coletar 3 informações do usuário para abrir um chamado:
    1. Nome
    2. Setor (ex: Financeiro, RH, TI...)
    3. Descrição detalhada do problema.
    
    Histórico da conversa até agora:
    {conversa_texto}
    
    Instruções:
    - Se faltar alguma informação, pergunte uma de cada vez.
    - Se o usuário já informou tudo, responda APENAS com a palavra chave: "FIM_DA_ENTREVISTA".
    - Caso contrário, continue a conversa naturalmente.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Desculpe, estou com dificuldade de conexão. Pode repetir?"
    
def extrair_dados_chat(historico_conversa):
    #Lê o histórico completo e transforma em JSON para salvar no banco.
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    conversa_texto = "\n".join(historico_conversa)
    
    prompt = f"""
    Analise a seguinte conversa de suporte técnico:
    {conversa_texto}
    
    Extraia as informações finais e retorne APENAS um JSON com estas chaves:
    1. "resumo": Um título curto para o problema (ex: "Falha na Impressora").
    2. "descricao_completa": Um texto contendo o nome do usuário, setor e o relato do problema.
    3. "categoria": Escolha uma (HARDWARE, SOFTWARE, REDE, OUTRO).
    4. "prioridade": Escolha uma (BAIXA, MEDIA, ALTA).
    5. "sugestao_ia": Uma sugestão técnica baseada no problema relatado.
    
    Responda apenas o JSON.
    """
    
    try:
        response = model.generate_content(prompt)
        texto = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)
    except:
        return {
            "resumo": "Chamado via Chat",
            "descricao_completa": conversa_texto,
            "categoria": "OUTRO",
            "prioridade": "MEDIA",
            "sugestao_ia": "Verificar histórico do chat."
        }