"""
Agente Conselheiro - Gera mensagens claras e acionáveis para o corretor
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from agno.agent import Agent
from agno.models.google import Gemini
from models import Evento, Lead
from tools import (
    WhatsAppSender,
    MessageComposer,
    TimingOptimizer,
    ContextLoader,
    MessageTemplates,
)


class AgenteConselheiro:
    """
    O Conselheiro transforma alertas e insights em mensagens 
    claras e acionáveis para o corretor via WhatsApp.
    
    É o único agente que fala diretamente com o usuário final.
    """
    
    INSTRUCTIONS = """
Você é o Conselheiro da Lastro. Você transforma alertas e insights em 
mensagens claras e acionáveis para o corretor via WhatsApp.

REGRAS DE COMUNICAÇÃO:

1. Seja direto. Nada de "Olá, tudo bem?" — vá direto ao ponto.

2. Sempre inclua o próximo passo concreto. Não diga apenas "fulano não respondeu",
   diga "fulano não respondeu — sugestão de mensagem: [texto pronto]"

3. Use dados específicos, não generalidades.
   ❌ "Alguns leads estão esperando"
   ✅ "3 leads com score 8+ estão há 24h+ sem resposta"

4. Quando sugerir mensagem para o corretor enviar ao cliente, 
   escreva ela PRONTA PARA COPIAR, entre aspas.

5. Respeite o contexto — não mande alerta de lead frio às 23h.

6. Agrupe quando possível — melhor uma mensagem com 3 itens 
   do que 3 mensagens separadas.

7. Use emojis com parcimônia (apenas para categorizar):
   🔔 novos leads
   ⏰ urgências de tempo
   📊 métricas
   💡 insights
   📈 destaques positivos
   📉 pontos de atenção

TOM DE VOZ: Colega experiente, pragmático, zero enrolação.

Você não é um assistente formal. Você é um parceiro de trabalho direto.
"""
    
    def __init__(
        self,
        memory_service,
        twilio_client=None
    ):
        self.memory = memory_service
        
        # Inicializa ferramentas
        self.tools = {
            "whatsapp_sender": WhatsAppSender(twilio_client),
            "message_composer": MessageComposer(MessageTemplates()),
            "timing_optimizer": TimingOptimizer(memory_service),
            "context_loader": ContextLoader(memory_service),
            "templates": MessageTemplates(),
        }
        
        # Cria agente Agno
        self.agent = Agent(
            name="Conselheiro",
            model=Gemini(id="gemini-2.5-flash"),
            instructions=self.INSTRUCTIONS,
            tools=[],  # TODO: Converter tools
            markdown=True,
        )
    
    async def comunicar_evento(
        self,
        corretor_id: str,
        evento: Evento
    ) -> Dict[str, Any]:
        """
        Comunica um evento ao corretor
        
        Returns:
            {
                "enviado": True,
                "mensagem": "...",
                "horario": "...",
                "agendado": False
            }
        """
        # Carrega contexto
        contexto = await self.tools["context_loader"].execute(
            corretor_id,
            lead_id=evento.lead_id
        )
        
        # Compõe mensagem baseada no tipo de evento
        mensagem = await self._compor_mensagem_evento(evento, contexto)
        
        # Verifica timing
        timing = await self.tools["timing_optimizer"].execute(
            corretor_id,
            urgencia=evento.urgencia.value
        )
        
        # Envia ou agenda
        if timing["enviar_agora"]:
            corretor = await self.memory.get_corretor(corretor_id)
            resultado = await self.tools["whatsapp_sender"].execute(
                corretor.telefone,
                mensagem
            )
            return {
                "enviado": True,
                "mensagem": mensagem,
                "horario": resultado["horario_envio"],
                "agendado": False
            }
        else:
            # Agenda para depois
            return {
                "enviado": False,
                "mensagem": mensagem,
                "horario": timing["horario_recomendado"],
                "agendado": True,
                "motivo": timing["motivo"]
            }
    
    async def comunicar_resumo_diario(
        self,
        corretor_id: str,
        briefing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envia resumo diário ao corretor
        """
        mensagem = self._formatar_resumo_diario(briefing)
        
        corretor = await self.memory.get_corretor(corretor_id)
        resultado = await self.tools["whatsapp_sender"].execute(
            corretor.telefone,
            mensagem
        )
        
        return {
            "enviado": True,
            "tipo": "resumo_diario",
            "mensagem": mensagem,
            "horario": resultado["horario_envio"]
        }
    
    async def comunicar_resumo_semanal(
        self,
        corretor_id: str,
        relatorio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envia resumo semanal ao corretor
        """
        mensagem = self._formatar_resumo_semanal(relatorio)
        
        corretor = await self.memory.get_corretor(corretor_id)
        resultado = await self.tools["whatsapp_sender"].execute(
            corretor.telefone,
            mensagem
        )
        
        return {
            "enviado": True,
            "tipo": "resumo_semanal",
            "mensagem": mensagem,
            "horario": resultado["horario_envio"]
        }
    
    async def comunicar_padrao_detectado(
        self,
        corretor_id: str,
        padrao: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Comunica padrão emergente detectado
        """
        mensagem = self._formatar_padrao(padrao)
        
        timing = await self.tools["timing_optimizer"].execute(
            corretor_id,
            urgencia="media"
        )
        
        if timing["enviar_agora"]:
            corretor = await self.memory.get_corretor(corretor_id)
            resultado = await self.tools["whatsapp_sender"].execute(
                corretor.telefone,
                mensagem
            )
            return {
                "enviado": True,
                "mensagem": mensagem,
                "horario": resultado["horario_envio"]
            }
        
        return {
            "enviado": False,
            "mensagem": mensagem,
            "agendado": True,
            "horario": timing["horario_recomendado"]
        }
    
    async def sugerir_mensagem_para_lead(
        self,
        lead: Lead,
        contexto: str
    ) -> str:
        """
        Gera sugestão de mensagem para o corretor enviar ao lead
        """
        # TODO: Usar LLM para gerar mensagem contextual e personalizada
        
        # Por enquanto, template simples
        if "financiamento" in lead.busca.caracteristicas:
            return f"""Oi {lead.nome.split()[0]}! Vi que você perguntou sobre financiamento.

Tenho boas notícias: esse imóvel aceita até 80% financiado.

Quer que eu te mande uma simulação com as taxas atuais?"""
        
        return f"""Oi {lead.nome.split()[0]}! Ainda interessado no imóvel?

Tenho algumas opções que se encaixam no que você busca.

Quando podemos conversar?"""
    
    async def _compor_mensagem_evento(
        self,
        evento: Evento,
        contexto: Dict[str, Any]
    ) -> str:
        """Compõe mensagem baseada no tipo de evento"""
        
        if evento.tipo == "novo_lead":
            return self._formatar_novo_lead(evento)
        
        elif evento.tipo == "lead_sem_resposta":
            return await self._formatar_lead_sem_resposta(evento)
        
        elif evento.tipo == "visita_proxima":
            return self._formatar_visita_proxima(evento)
        
        elif evento.tipo == "cliente_urgente":
            return self._formatar_cliente_urgente(evento)
        
        else:
            # Formato genérico
            return f"""🔔 {evento.titulo}

{evento.descricao}

{evento.acao_recomendada or ''}"""
    
    def _formatar_novo_lead(self, evento: Evento) -> str:
        """Formata mensagem de novo lead"""
        metadata = evento.metadata
        
        return f"""🔔 Novo lead: {metadata.get('nome', 'Nome não informado')}

Origem: {metadata.get('origem', 'N/A')}
Interesse: {metadata.get('imovel_interesse', metadata.get('descricao_busca', 'Não especificado'))}

💡 Responder em até 5min aumenta conversão em 9x

{evento.acao_recomendada or 'Fazer primeiro contato'}"""
    
    async def _formatar_lead_sem_resposta(self, evento: Evento) -> str:
        """Formata mensagem de lead sem resposta"""
        metadata = evento.metadata
        lead_id = evento.lead_id
        
        # Busca lead completo
        lead = await self.memory.get_lead(lead_id)
        
        # Gera sugestão de mensagem
        sugestao = await self.sugerir_mensagem_para_lead(
            lead,
            contexto=evento.descricao
        )
        
        return f"""⏰ {metadata['nome']} não recebeu resposta há {metadata['horas_sem_resposta']}h

Score: {metadata['score']}/10
{evento.descricao}

Sugestão de mensagem:
"{sugestao}"

Enviar?"""
    
    def _formatar_visita_proxima(self, evento: Evento) -> str:
        """Formata lembrete de visita"""
        metadata = evento.metadata
        
        return f"""⏰ Visita em {metadata['minutos_ate']} minutos

Cliente: {metadata['lead_nome']}
Local: {metadata['imovel']}

Tudo pronto?"""
    
    def _formatar_cliente_urgente(self, evento: Evento) -> str:
        """Formata alerta de cliente urgente"""
        return f"""🔔 URGENTE: {evento.titulo}

{evento.descricao}

{evento.acao_recomendada}"""
    
    def _formatar_resumo_diario(self, briefing: Dict[str, Any]) -> str:
        """Formata resumo do dia"""
        metricas = briefing.get("metricas", {})
        insights = briefing.get("insights", [])
        
        msg = f"""📊 Resumo do dia ({briefing['periodo']}):

"""
        
        if metricas:
            msg += f"""Leads novos: {metricas.get('leads_novos', 0)}
Conversas: {metricas.get('conversas_totais', 0)}
Visitas: {metricas.get('visitas_agendadas', 0)}

"""
        
        if insights:
            msg += "💡 Insights:\n"
            for insight in insights[:3]:  # Top 3
                msg += f"• {insight}\n"
        
        return msg.strip()
    
    def _formatar_resumo_semanal(self, relatorio: Dict[str, Any]) -> str:
        """Formata resumo semanal"""
        metricas = relatorio.get("metricas", {})
        destaques = relatorio.get("destaques", [])
        areas_atencao = relatorio.get("areas_atencao", [])
        
        msg = f"""📊 Sua semana ({relatorio.get('periodo', '')}):

{metricas.get('leads_novos', 0)} leads | {metricas.get('conversas_totais', 0)} conversas | {metricas.get('visitas_agendadas', 0)} visitas | {metricas.get('propostas_enviadas', 0)} propostas

"""
        
        if destaques:
            msg += "📈 Destaques:\n"
            for destaque in destaques[:2]:
                msg += f"• {destaque}\n"
            msg += "\n"
        
        if areas_atencao:
            msg += "📉 Atenção:\n"
            for area in areas_atencao[:2]:
                msg += f"• {area}\n"
            msg += "\n"
        
        msg += "Quer ver a análise completa?"
        
        return msg
    
    def _formatar_padrao(self, padrao: Dict[str, Any]) -> str:
        """Formata padrão detectado"""
        return f"""💡 Padrão detectado:

{padrao['descricao']}

Relevância: {padrao.get('relevancia', 'média')}

Oportunidade: revisar carteira para atender essa demanda"""
