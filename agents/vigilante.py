"""
Agente Vigilante - Monitora continuamente fontes de dados e detecta eventos
"""
from typing import List, Dict, Any
from datetime import datetime
from agno.agent import Agent
from agno.models.google import Gemini
from models import Evento, EventoTipo, EventoUrgencia
from tools import (
    WhatsAppMonitor,
    PortalMonitor,
    CalendarCheck,
    LeadStatusCheck,
    ImovelMonitor,
)


class AgenteVigilante:
    """
    O Vigilante monitora todas as entradas de dados do corretor 
    e identifica eventos que merecem atenção.
    
    Nunca fala diretamente com o corretor - reporta ao Orquestrador.
    """
    
    INSTRUCTIONS = """
Você é o Vigilante da Lastro. Seu trabalho é monitorar todas as entradas 
de dados do corretor e identificar eventos que merecem atenção. 

Você nunca fala diretamente com o corretor — você reporta ao Orquestrador.

Eventos que você deve detectar:
- Novo lead chegou (de qualquer fonte)
- Lead não recebeu resposta há mais de X horas
- Cliente mencionou urgência ou prazo
- Padrão de busca emergente (múltiplas pessoas pedindo coisa similar)
- Imóvel da carteira teve mudança de preço
- Visita agendada se aproximando
- Cliente que visitou imóvel há mais de 5 dias sem follow-up

Para cada evento, você deve:
1. Classificar a urgência (alta/média/baixa)
2. Identificar o tipo de ação recomendada
3. Extrair o contexto relevante
4. Reportar de forma estruturada ao Orquestrador

Seja objetivo e preciso. Sua função é detectar, não decidir.
"""
    
    def __init__(
        self,
        memory_service,
        twilio_client=None
    ):
        self.memory = memory_service
        
        # Inicializa ferramentas
        self.tools = {
            "whatsapp_monitor": WhatsAppMonitor(twilio_client),
            "portal_monitor": PortalMonitor(),
            "calendar_check": CalendarCheck(),
            "lead_status_check": LeadStatusCheck(memory_service),
            "imovel_monitor": ImovelMonitor(),
        }
        
        # Cria agente Agno
        self.agent = Agent(
            name="Vigilante",
            model=Gemini(id="gemini-2.5-flash"),
            instructions=self.INSTRUCTIONS,
            tools=[],  # TODO: Converter tools para formato Agno
            markdown=True,
        )
    
    async def monitorar_corretor(
        self, 
        corretor_id: str
    ) -> List[Evento]:
        """
        Executa ciclo completo de monitoramento para um corretor
        
        Returns:
            Lista de eventos detectados
        """
        eventos = []
        
        # 1. Verifica novas mensagens no WhatsApp
        msgs_result = await self.tools["whatsapp_monitor"].execute(corretor_id)
        eventos.extend(
            self._processar_novas_mensagens(corretor_id, msgs_result)
        )
        
        # 2. Verifica novos leads de portais
        portal_result = await self.tools["portal_monitor"].execute(corretor_id)
        eventos.extend(
            self._processar_novos_leads(corretor_id, portal_result)
        )
        
        # 3. Verifica leads sem resposta
        status_result = await self.tools["lead_status_check"].execute(
            corretor_id,
            horas_sem_resposta=24
        )
        eventos.extend(
            self._processar_leads_pendentes(corretor_id, status_result)
        )
        
        # 4. Verifica compromissos próximos
        calendar_result = await self.tools["calendar_check"].execute(
            corretor_id,
            horas_antecedencia=2
        )
        eventos.extend(
            self._processar_compromissos(corretor_id, calendar_result)
        )
        
        # 5. Verifica mudanças em imóveis
        imovel_result = await self.tools["imovel_monitor"].execute(corretor_id)
        eventos.extend(
            self._processar_mudancas_imoveis(corretor_id, imovel_result)
        )
        
        return eventos
    
    def _processar_novas_mensagens(
        self, 
        corretor_id: str, 
        resultado: Dict[str, Any]
    ) -> List[Evento]:
        """Processa novas mensagens e cria eventos"""
        eventos = []
        
        for msg in resultado.get("novas_mensagens", []):
            # Verifica se é lead novo ou existente
            lead_id = msg.get("lead_id")
            
            if not lead_id:
                # Novo lead detectado
                evento = Evento(
                    id=f"evt_{datetime.utcnow().timestamp()}",
                    tipo=EventoTipo.NOVO_LEAD,
                    urgencia=EventoUrgencia.ALTA,
                    corretor_id=corretor_id,
                    titulo=f"Nova mensagem de {msg['nome']}",
                    descricao=f"Primeira mensagem: {msg['conteudo'][:100]}...",
                    acao_recomendada="Responder em até 5 minutos",
                    metadata=msg
                )
                eventos.append(evento)
        
        return eventos
    
    def _processar_novos_leads(
        self, 
        corretor_id: str, 
        resultado: Dict[str, Any]
    ) -> List[Evento]:
        """Processa novos leads de portais"""
        eventos = []
        
        for lead in resultado.get("novos_leads", []):
            evento = Evento(
                id=f"evt_{datetime.utcnow().timestamp()}",
                tipo=EventoTipo.NOVO_LEAD,
                urgencia=EventoUrgencia.ALTA,
                corretor_id=corretor_id,
                titulo=f"Novo lead: {lead['nome']} ({lead['origem']})",
                descricao=f"Interesse: {lead.get('imovel_interesse', 'Não especificado')}",
                acao_recomendada="Fazer primeiro contato imediatamente",
                metadata=lead
            )
            eventos.append(evento)
        
        return eventos
    
    def _processar_leads_pendentes(
        self, 
        corretor_id: str, 
        resultado: Dict[str, Any]
    ) -> List[Evento]:
        """Processa leads que precisam de follow-up"""
        eventos = []
        
        for lead in resultado.get("leads_pendentes", []):
            # Apenas leads com score alto (>=7) viram evento de urgência
            if lead["score"] >= 7:
                urgencia = EventoUrgencia.ALTA
            elif lead["score"] >= 5:
                urgencia = EventoUrgencia.MEDIA
            else:
                urgencia = EventoUrgencia.BAIXA
            
            evento = Evento(
                id=f"evt_{datetime.utcnow().timestamp()}",
                tipo=EventoTipo.LEAD_SEM_RESPOSTA,
                urgencia=urgencia,
                corretor_id=corretor_id,
                lead_id=lead["lead_id"],
                titulo=f"{lead['nome']} sem resposta há {lead['horas_sem_resposta']}h",
                descricao=f"Score: {lead['score']}/10. {lead['contexto']}",
                acao_recomendada="Enviar follow-up personalizado",
                metadata=lead
            )
            eventos.append(evento)
        
        return eventos
    
    def _processar_compromissos(
        self, 
        corretor_id: str, 
        resultado: Dict[str, Any]
    ) -> List[Evento]:
        """Processa compromissos próximos"""
        eventos = []
        
        for compromisso in resultado.get("compromissos_proximos", []):
            minutos = compromisso["minutos_ate"]
            
            if minutos <= 30:
                urgencia = EventoUrgencia.ALTA
            elif minutos <= 60:
                urgencia = EventoUrgencia.MEDIA
            else:
                urgencia = EventoUrgencia.BAIXA
            
            evento = Evento(
                id=f"evt_{datetime.utcnow().timestamp()}",
                tipo=EventoTipo.VISITA_PROXIMA,
                urgencia=urgencia,
                corretor_id=corretor_id,
                titulo=f"Visita em {minutos}min: {compromisso['lead_nome']}",
                descricao=f"Local: {compromisso['imovel']}",
                acao_recomendada="Confirmar presença",
                metadata=compromisso
            )
            eventos.append(evento)
        
        return eventos
    
    def _processar_mudancas_imoveis(
        self, 
        corretor_id: str, 
        resultado: Dict[str, Any]
    ) -> List[Evento]:
        """Processa mudanças na carteira de imóveis"""
        eventos = []
        
        for mudanca in resultado.get("mudancas", []):
            evento = Evento(
                id=f"evt_{datetime.utcnow().timestamp()}",
                tipo=EventoTipo.IMOVEL_MUDANCA_PRECO,
                urgencia=EventoUrgencia.MEDIA,
                corretor_id=corretor_id,
                titulo=f"Imóvel {mudanca['imovel_id']} - {mudanca['tipo_mudanca']}",
                descricao=f"De {mudanca['valor_anterior']} para {mudanca['valor_novo']}",
                acao_recomendada="Revisar estratégia de venda",
                metadata=mudanca
            )
            eventos.append(evento)
        
        return eventos
