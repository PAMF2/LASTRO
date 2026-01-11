"""
Ferramentas de comunicação - usadas pelo Agente Conselheiro
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, time
from .base import BaseTool


class WhatsAppSender(BaseTool):
    """Envia mensagens via WhatsApp"""
    
    def __init__(self, twilio_client):
        super().__init__()
        self.twilio_client = twilio_client
    
    async def execute(
        self, 
        destinatario: str,  # número do corretor
        mensagem: str,
        midia_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem pelo WhatsApp
        
        Args:
            destinatario: Número do WhatsApp (formato: +5511999998888)
            mensagem: Texto da mensagem
            midia_url: URL de imagem/documento (opcional)
        
        Returns:
            {
                "sucesso": True,
                "message_sid": "SM...",
                "horario_envio": "2026-01-11 10:30:00",
                "status": "enviado"
            }
        """
        # TODO: Implementar envio real via Twilio
        return {
            "sucesso": True,
            "message_sid": "SM_mock_123",
            "horario_envio": datetime.utcnow().isoformat(),
            "status": "enviado"
        }


class MessageComposer(BaseTool):
    """Compõe mensagens a partir de templates"""
    
    def __init__(self, template_service):
        super().__init__()
        self.templates = template_service
    
    async def execute(
        self,
        tipo_mensagem: str,  # novo_lead, follow_up, resumo_semanal
        variaveis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gera mensagem formatada
        
        Args:
            tipo_mensagem: Tipo do template
            variaveis: Dados para preencher template
        
        Returns:
            {
                "mensagem": "🔔 Novo lead: Maria Silva\n3q Pinheiros, 800k-1M...",
                "template_usado": "novo_lead_v2",
                "tom": "direto"
            }
        """
        template = await self.templates.get_template(tipo_mensagem)
        mensagem = template.format(**variaveis)
        
        return {
            "mensagem": mensagem,
            "template_usado": tipo_mensagem,
            "tom": "direto"
        }


class TimingOptimizer(BaseTool):
    """Otimiza o horário de envio de mensagens"""
    
    def __init__(self, memory_service):
        super().__init__()
        self.memory = memory_service
    
    async def execute(
        self,
        corretor_id: str,
        urgencia: str = "media",  # baixa, media, alta
        horario_atual: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Determina o melhor horário para enviar mensagem
        
        Args:
            corretor_id: ID do corretor
            urgencia: Urgência da mensagem
            horario_atual: Horário de referência (default: agora)
        
        Returns:
            {
                "enviar_agora": True/False,
                "horario_recomendado": "2026-01-11 10:00:00",
                "motivo": "Horário comercial preferencial do corretor",
                "aguardar_minutos": 0
            }
        """
        if horario_atual is None:
            horario_atual = datetime.utcnow()
        
        # Busca preferências do corretor
        corretor = await self.memory.get_corretor(corretor_id)
        
        # Urgência alta envia imediatamente
        if urgencia == "alta":
            return {
                "enviar_agora": True,
                "horario_recomendado": horario_atual.isoformat(),
                "motivo": "Urgência alta",
                "aguardar_minutos": 0
            }
        
        # Verifica se está no horário comercial do corretor
        hora_inicio = time.fromisoformat(corretor.preferencias.horario_inicio)
        hora_fim = time.fromisoformat(corretor.preferencias.horario_fim)
        hora_atual = horario_atual.time()
        
        dentro_horario = hora_inicio <= hora_atual <= hora_fim
        
        if dentro_horario:
            return {
                "enviar_agora": True,
                "horario_recomendado": horario_atual.isoformat(),
                "motivo": "Dentro do horário preferencial",
                "aguardar_minutos": 0
            }
        
        # Fora do horário - agendar para próximo horário
        proximo_horario = horario_atual.replace(
            hour=hora_inicio.hour,
            minute=hora_inicio.minute,
            second=0
        )
        
        if proximo_horario <= horario_atual:
            # Adiciona 1 dia
            from datetime import timedelta
            proximo_horario += timedelta(days=1)
        
        minutos_espera = int((proximo_horario - horario_atual).total_seconds() / 60)
        
        return {
            "enviar_agora": False,
            "horario_recomendado": proximo_horario.isoformat(),
            "motivo": "Fora do horário comercial do corretor",
            "aguardar_minutos": minutos_espera
        }


class ContextLoader(BaseTool):
    """Carrega contexto recente para personalizar mensagens"""
    
    def __init__(self, memory_service):
        super().__init__()
        self.memory = memory_service
    
    async def execute(
        self,
        corretor_id: str,
        lead_id: Optional[str] = None,
        dias_historico: int = 7
    ) -> Dict[str, Any]:
        """
        Carrega contexto relevante
        
        Returns:
            {
                "ultimas_interacoes": [
                    {
                        "com": "Maria Silva",
                        "quando": "hoje às 09:15",
                        "assunto": "Perguntou sobre financiamento"
                    }
                ],
                "alertas_recentes": [
                    "Você tem 3 leads sem resposta há mais de 24h"
                ],
                "performance_recente": {
                    "leads_novos_hoje": 2,
                    "visitas_proximas": 1
                }
            }
        """
        # TODO: Carregar contexto completo do corretor
        return {
            "ultimas_interacoes": [],
            "alertas_recentes": [],
            "performance_recente": {}
        }


class MessageTemplates(BaseTool):
    """Gerencia templates de mensagens"""
    
    TEMPLATES = {
        "novo_lead": """🔔 Novo lead: {nome}
{descricao_busca}

💡 Responder em até 5min aumenta conversão em 9x

Sugestão de resposta:
"{sugestao_mensagem}"
""",
        
        "lead_sem_resposta": """⏰ {nome} ({descricao_lead}) não recebeu resposta há {horas}h

{contexto_lead}

Sugestão:
"{sugestao_mensagem}"

Enviar?""",
        
        "resumo_semanal": """📊 Sua semana ({periodo}):

{metricas}

📈 Destaque: {destaque}
📉 Atenção: {atencao}

💡 Insight: {insight}

{call_to_action}""",
        
        "padrao_detectado": """💡 Padrão detectado:

{descricao_padrao}

Oportunidade: {oportunidade}

{sugestao_acao}"""
    }
    
    async def execute(self, template_name: str) -> str:
        """Retorna template por nome"""
        return self.TEMPLATES.get(template_name, "")
    
    async def get_template(self, name: str) -> str:
        """Alias para execute"""
        return await self.execute(name)


class NotificationScheduler(BaseTool):
    """Agenda notificações para envio futuro"""
    
    def __init__(self):
        super().__init__()
        self.queue = []  # Em produção, usar Redis/Celery
    
    async def execute(
        self,
        destinatario: str,
        mensagem: str,
        horario_envio: datetime,
        prioridade: int = 5  # 1-10
    ) -> Dict[str, Any]:
        """
        Agenda mensagem para envio futuro
        
        Returns:
            {
                "agendado": True,
                "job_id": "job_123",
                "horario_envio": "2026-01-11 14:00:00",
                "posicao_fila": 3
            }
        """
        job = {
            "destinatario": destinatario,
            "mensagem": mensagem,
            "horario_envio": horario_envio,
            "prioridade": prioridade
        }
        
        self.queue.append(job)
        
        return {
            "agendado": True,
            "job_id": f"job_{len(self.queue)}",
            "horario_envio": horario_envio.isoformat(),
            "posicao_fila": len(self.queue)
        }
