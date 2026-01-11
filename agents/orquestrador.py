"""
Orquestrador - Coordena os três agentes e gerencia prioridades
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from agno.agent import Agent
from agno.models.google import Gemini
from agno.os import AgentOS
from models import Evento, EventoUrgencia
from .vigilante import AgenteVigilante
from .analista import AgenteAnalista
from .conselheiro import AgenteConselheiro


class Orquestrador:
    """
    O Orquestrador coordena o Vigilante, o Analista e o Conselheiro 
    para entregar valor máximo ao corretor com mínimo ruído.
    
    Age como Team Lead dos agentes.
    """
    
    INSTRUCTIONS = """
Você é o Orquestrador da Lastro. Você coordena o Vigilante, o Analista 
e o Conselheiro para entregar valor máximo ao corretor com mínimo ruído.

SUAS RESPONSABILIDADES:

1. Receber alertas do Vigilante e decidir se merecem ação imediata
2. Solicitar análises ao Analista quando necessário
3. Instruir o Conselheiro sobre o que comunicar e quando
4. Evitar sobrecarga — não bombardear o corretor com mensagens
5. Priorizar por impacto: lead quente > insight estratégico > lembrete rotineiro

REGRAS DE PRIORIZAÇÃO:

1. Máximo 5 mensagens por dia ao corretor (exceto se ele pedir mais)
2. Leads quentes (< 1h sem resposta) têm prioridade máxima
3. Agrupe alertas similares sempre que possível
4. Horário comercial preferencial (8h-21h), exceto urgências
5. Não interrompa o corretor em visitas ou reuniões (verificar calendário)

CRITÉRIOS DE URGÊNCIA:

ALTA (enviar imediatamente):
- Novo lead de portal (primeiros 5 minutos são críticos)
- Lead quente sem resposta há > 24h e score >= 8
- Compromisso em < 30min
- Cliente mencionou urgência explícita

MÉDIA (agrupar e enviar no próximo horário ótimo):
- Lead morno sem resposta há > 48h
- Padrão emergente detectado
- Insight estratégico relevante

BAIXA (incluir no resumo diário):
- Leads frios sem resposta
- Métricas de rotina
- Insights informativos

Seja estratégico: melhor uma comunicação certeira do que muitas irrelevantes.
"""
    
    def __init__(
        self,
        memory_service,
        twilio_client=None
    ):
        self.memory = memory_service
        
        # Inicializa os três agentes
        self.vigilante = AgenteVigilante(memory_service, twilio_client)
        self.analista = AgenteAnalista(memory_service)
        self.conselheiro = AgenteConselheiro(memory_service, twilio_client)
        
        # Cria AgentOS com os três agentes
        self.agent_os = AgentOS(
            agents=[
                self.vigilante.agent,
                self.analista.agent,
                self.conselheiro.agent,
            ]
        )
        
        # Controle de mensagens enviadas
        self.mensagens_hoje = {}  # corretor_id -> count
    
    async def processar_corretor(
        self, 
        corretor_id: str
    ) -> Dict[str, Any]:
        """
        Executa ciclo completo de processamento para um corretor
        
        1. Vigilante detecta eventos
        2. Orquestrador prioriza e decide ações
        3. Analista gera insights quando necessário
        4. Conselheiro comunica ao corretor
        
        Returns:
            {
                "eventos_detectados": 5,
                "eventos_processados": 3,
                "mensagens_enviadas": 2,
                "mensagens_agendadas": 1,
                "insights_gerados": 1
            }
        """
        resultado = {
            "eventos_detectados": 0,
            "eventos_processados": 0,
            "mensagens_enviadas": 0,
            "mensagens_agendadas": 0,
            "insights_gerados": 0
        }
        
        # 1. Vigilante detecta eventos
        eventos = await self.vigilante.monitorar_corretor(corretor_id)
        resultado["eventos_detectados"] = len(eventos)
        
        if not eventos:
            return resultado
        
        # 2. Prioriza eventos
        eventos_priorizados = self._priorizar_eventos(eventos)
        
        # 3. Verifica limite de mensagens do dia
        corretor = await self.memory.get_corretor(corretor_id)
        limite_diario = corretor.preferencias.max_mensagens_dia
        mensagens_enviadas_hoje = self._contar_mensagens_hoje(corretor_id)
        
        # 4. Processa eventos de acordo com prioridade
        for evento in eventos_priorizados:
            if mensagens_enviadas_hoje >= limite_diario:
                # Agenda para amanhã
                await self._agendar_evento(corretor_id, evento)
                resultado["mensagens_agendadas"] += 1
                continue
            
            # Decide se envia ou agrupa
            if self._deve_enviar_imediato(evento):
                # Envia imediatamente
                resultado_envio = await self.conselheiro.comunicar_evento(
                    corretor_id,
                    evento
                )
                
                if resultado_envio["enviado"]:
                    resultado["mensagens_enviadas"] += 1
                    mensagens_enviadas_hoje += 1
                    self._registrar_mensagem_enviada(corretor_id)
                elif resultado_envio["agendado"]:
                    resultado["mensagens_agendadas"] += 1
                
                resultado["eventos_processados"] += 1
            else:
                # Agrupa para envio posterior
                await self._adicionar_a_fila_agrupamento(corretor_id, evento)
        
        return resultado
    
    async def gerar_resumo_diario(
        self, 
        corretor_id: str,
        horario: str = "manha"  # manha ou noite
    ) -> Dict[str, Any]:
        """
        Gera e envia resumo diário
        """
        # Solicita briefing ao Analista
        briefing = await self.analista.gerar_briefing_diario(corretor_id)
        
        # Adiciona eventos pendentes da fila de agrupamento
        eventos_pendentes = await self._obter_eventos_agrupados(corretor_id)
        briefing["eventos_pendentes"] = eventos_pendentes
        
        # Conselheiro comunica
        resultado = await self.conselheiro.comunicar_resumo_diario(
            corretor_id,
            briefing
        )
        
        # Limpa fila de agrupamento
        await self._limpar_fila_agrupamento(corretor_id)
        
        return resultado
    
    async def gerar_resumo_semanal(
        self, 
        corretor_id: str
    ) -> Dict[str, Any]:
        """
        Gera e envia resumo semanal
        """
        # Solicita relatório ao Analista
        relatorio = await self.analista.gerar_relatorio_semanal(corretor_id)
        
        # Conselheiro comunica
        resultado = await self.conselheiro.comunicar_resumo_semanal(
            corretor_id,
            relatorio
        )
        
        return resultado
    
    async def detectar_e_comunicar_padroes(
        self, 
        corretor_id: str
    ) -> List[Dict[str, Any]]:
        """
        Detecta padrões e comunica os mais relevantes
        """
        # Analista detecta padrões
        padroes = await self.analista.detectar_padroes(corretor_id, dias=7)
        
        resultados = []
        
        # Comunica apenas padrões de alta relevância
        for padrao in padroes:
            if padrao["relevancia"] == "alta":
                resultado = await self.conselheiro.comunicar_padrao_detectado(
                    corretor_id,
                    padrao
                )
                resultados.append(resultado)
        
        return resultados
    
    def _priorizar_eventos(
        self, 
        eventos: List[Evento]
    ) -> List[Evento]:
        """
        Ordena eventos por prioridade
        
        Critérios:
        1. Urgência (alta > media > baixa)
        2. Tipo (novo_lead > lead_sem_resposta > outros)
        3. Score do lead (se aplicável)
        """
        def chave_prioridade(evento: Evento) -> tuple:
            # Peso da urgência
            urgencia_peso = {
                EventoUrgencia.ALTA: 3,
                EventoUrgencia.MEDIA: 2,
                EventoUrgencia.BAIXA: 1
            }
            
            # Peso do tipo
            tipo_peso = {
                "novo_lead": 10,
                "cliente_urgente": 9,
                "lead_sem_resposta": 8,
                "visita_proxima": 7,
                "padrao_detectado": 5,
                "imovel_mudanca_preco": 4,
                "follow_up_pendente": 3
            }
            
            # Score do lead (se existir no metadata)
            score = evento.metadata.get("score", 0)
            
            return (
                urgencia_peso.get(evento.urgencia, 0),
                tipo_peso.get(evento.tipo.value, 0),
                score
            )
        
        return sorted(eventos, key=chave_prioridade, reverse=True)
    
    def _deve_enviar_imediato(self, evento: Evento) -> bool:
        """Decide se evento merece envio imediato"""
        # Urgência alta sempre envia
        if evento.urgencia == EventoUrgencia.ALTA:
            return True
        
        # Novos leads sempre enviam
        if evento.tipo.value == "novo_lead":
            return True
        
        # Cliente urgente sempre envia
        if evento.tipo.value == "cliente_urgente":
            return True
        
        # Visita em menos de 1h
        if evento.tipo.value == "visita_proxima":
            minutos = evento.metadata.get("minutos_ate", 999)
            if minutos < 60:
                return True
        
        # Lead quente sem resposta
        if evento.tipo.value == "lead_sem_resposta":
            score = evento.metadata.get("score", 0)
            if score >= 8:
                return True
        
        return False
    
    def _contar_mensagens_hoje(self, corretor_id: str) -> int:
        """Conta quantas mensagens foram enviadas hoje"""
        hoje = datetime.utcnow().date()
        key = f"{corretor_id}_{hoje}"
        return self.mensagens_hoje.get(key, 0)
    
    def _registrar_mensagem_enviada(self, corretor_id: str):
        """Registra que uma mensagem foi enviada"""
        hoje = datetime.utcnow().date()
        key = f"{corretor_id}_{hoje}"
        self.mensagens_hoje[key] = self.mensagens_hoje.get(key, 0) + 1
    
    async def _agendar_evento(self, corretor_id: str, evento: Evento):
        """Agenda evento para processamento futuro"""
        # TODO: Implementar com Redis/Celery
        pass
    
    async def _adicionar_a_fila_agrupamento(
        self, 
        corretor_id: str, 
        evento: Evento
    ):
        """Adiciona evento à fila de agrupamento para envio posterior"""
        # TODO: Implementar fila de agrupamento
        pass
    
    async def _obter_eventos_agrupados(
        self, 
        corretor_id: str
    ) -> List[Evento]:
        """Obtém eventos que foram agrupados"""
        # TODO: Implementar
        return []
    
    async def _limpar_fila_agrupamento(self, corretor_id: str):
        """Limpa fila de eventos agrupados"""
        # TODO: Implementar
        pass
