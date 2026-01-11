"""
Ferramentas de monitoramento - usadas pelo Agente Vigilante
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from .base import BaseTool
from models import Lead, Evento, EventoTipo, EventoUrgencia


class WhatsAppMonitor(BaseTool):
    """Monitora novas mensagens no WhatsApp do corretor"""
    
    def __init__(self, twilio_client):
        super().__init__()
        self.twilio_client = twilio_client
    
    async def execute(self, corretor_id: str) -> Dict[str, Any]:
        """
        Verifica novas mensagens não lidas no WhatsApp
        
        Returns:
            {
                "novas_mensagens": [
                    {
                        "remetente": "+5511999998888",
                        "nome": "Maria Silva",
                        "conteudo": "Oi, vi o anúncio...",
                        "horario": "2026-01-11 10:30:00",
                        "lead_id": "lead_abc123"
                    }
                ],
                "total": 3
            }
        """
        # TODO: Implementar integração real com Twilio/WhatsApp
        # Por enquanto, retorna mock
        return {
            "novas_mensagens": [],
            "total": 0
        }


class PortalMonitor(BaseTool):
    """Monitora novos leads vindos de portais imobiliários"""
    
    async def execute(self, corretor_id: str) -> Dict[str, Any]:
        """
        Verifica novos leads dos portais (ZAP, Viva Real, OLX)
        
        Returns:
            {
                "novos_leads": [
                    {
                        "nome": "João Santos",
                        "telefone": "+5511988887777",
                        "origem": "zap_imoveis",
                        "imovel_interesse": "Apartamento 3q Pinheiros",
                        "mensagem": "Gostaria de mais informações",
                        "horario": "2026-01-11 09:15:00"
                    }
                ],
                "total": 2
            }
        """
        # TODO: Implementar webhooks dos portais
        return {
            "novos_leads": [],
            "total": 0
        }


class CalendarCheck(BaseTool):
    """Verifica compromissos próximos no calendário"""
    
    async def execute(self, corretor_id: str, horas_antecedencia: int = 2) -> Dict[str, Any]:
        """
        Lista visitas e compromissos nas próximas X horas
        
        Args:
            corretor_id: ID do corretor
            horas_antecedencia: Quantas horas à frente verificar
        
        Returns:
            {
                "compromissos_proximos": [
                    {
                        "tipo": "visita",
                        "lead_nome": "Maria Silva",
                        "imovel": "Cobertura Itaim - Rua X, 123",
                        "horario": "2026-01-11 14:00:00",
                        "minutos_ate": 90
                    }
                ],
                "total": 1
            }
        """
        # TODO: Integrar com Google Calendar
        return {
            "compromissos_proximos": [],
            "total": 0
        }


class LeadStatusCheck(BaseTool):
    """Verifica status de leads e identifica os que precisam de follow-up"""
    
    def __init__(self, memory_service):
        super().__init__()
        self.memory = memory_service
    
    async def execute(
        self, 
        corretor_id: str, 
        horas_sem_resposta: int = 24
    ) -> Dict[str, Any]:
        """
        Identifica leads que não receberam resposta há muito tempo
        
        Args:
            corretor_id: ID do corretor
            horas_sem_resposta: Threshold de horas sem resposta
        
        Returns:
            {
                "leads_pendentes": [
                    {
                        "lead_id": "lead_abc123",
                        "nome": "Maria Silva",
                        "horas_sem_resposta": 26,
                        "score": 9,
                        "ultima_mensagem": "Tem financiamento?",
                        "contexto": "Lead quente, perguntou sobre financiamento"
                    }
                ],
                "total": 3
            }
        """
        # Busca todos os leads do corretor
        leads = await self.memory.get_leads_by_corretor(corretor_id)
        
        agora = datetime.utcnow()
        threshold = timedelta(hours=horas_sem_resposta)
        
        leads_pendentes = []
        
        for lead in leads:
            if lead.data_ultima_interacao:
                tempo_sem_resposta = agora - lead.data_ultima_interacao
                
                if tempo_sem_resposta > threshold:
                    # Última interação do lead (não do corretor)
                    ultima_msg = None
                    for interacao in reversed(lead.interacoes):
                        if interacao.tipo.value == "mensagem_recebida":
                            ultima_msg = interacao.conteudo
                            break
                    
                    leads_pendentes.append({
                        "lead_id": lead.id,
                        "nome": lead.nome,
                        "horas_sem_resposta": int(tempo_sem_resposta.total_seconds() / 3600),
                        "score": lead.score,
                        "ultima_mensagem": ultima_msg,
                        "contexto": lead.proximo_passo or "Aguardando resposta"
                    })
        
        # Ordena por score (mais quentes primeiro)
        leads_pendentes.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "leads_pendentes": leads_pendentes,
            "total": len(leads_pendentes)
        }


class ImovelMonitor(BaseTool):
    """Monitora mudanças na carteira de imóveis do corretor"""
    
    async def execute(self, corretor_id: str) -> Dict[str, Any]:
        """
        Detecta mudanças em imóveis da carteira (preço, status, etc)
        
        Returns:
            {
                "mudancas": [
                    {
                        "imovel_id": "imovel_123",
                        "tipo_mudanca": "preco",
                        "valor_anterior": 850000,
                        "valor_novo": 820000,
                        "data": "2026-01-11 08:00:00"
                    }
                ],
                "total": 1
            }
        """
        # TODO: Integrar com sistema de carteira de imóveis
        return {
            "mudancas": [],
            "total": 0
        }
