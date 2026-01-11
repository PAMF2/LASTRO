"""
Agente Analista - Processa dados históricos e gera insights estratégicos
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from agno.agent import Agent
from agno.models.google import Gemini
from tools import (
    ConversationAnalyzer,
    DemandAggregator,
    LeadScorer,
    PerformanceCalculator,
    ConversionTracker,
)


class AgenteAnalista:
    """
    O Analista processa dados históricos, identifica padrões 
    e gera insights estratégicos.
    
    Transforma dados brutos em insights acionáveis.
    """
    
    INSTRUCTIONS = """
Você é o Analista da Lastro. Seu trabalho é encontrar padrões nos dados 
do corretor que gerem vantagem competitiva. Você transforma dados brutos 
em insights acionáveis.

Análises que você faz:
- Quais horários têm melhor taxa de resposta
- Quais tipos de imóvel estão em alta demanda
- Quais abordagens de mensagem convertem mais
- Quais leads têm maior probabilidade de fechar
- Performance semanal comparada com semanas anteriores
- Gaps entre demanda dos clientes e carteira disponível

REGRA FUNDAMENTAL: Sempre quantifique seus insights.

❌ NÃO diga: "muitos clientes querem varanda"
✅ DIGA: "67% dos leads desta semana mencionaram varanda como requisito"

Seja preciso, baseado em dados, e foque em insights acionáveis.
Cada insight deve vir com um número ou percentual que o sustente.
"""
    
    def __init__(self, memory_service):
        self.memory = memory_service
        
        # Inicializa ferramentas
        self.tools = {
            "conversation_analyzer": ConversationAnalyzer(memory_service),
            "demand_aggregator": DemandAggregator(memory_service),
            "lead_scorer": LeadScorer(),
            "performance_calculator": PerformanceCalculator(memory_service),
            "conversion_tracker": ConversionTracker(),
        }
        
        # Cria agente Agno
        self.agent = Agent(
            name="Analista",
            model=Gemini(id="gemini-2.5-flash"),
            instructions=self.INSTRUCTIONS,
            tools=[],  # TODO: Converter tools
            markdown=True,
        )
    
    async def gerar_briefing_diario(
        self, 
        corretor_id: str
    ) -> Dict[str, Any]:
        """
        Gera briefing diário com principais insights
        
        Returns:
            {
                "periodo": "2026-01-11",
                "metricas": {...},
                "insights": [...],
                "acoes_recomendadas": [...]
            }
        """
        hoje = datetime.utcnow()
        
        # Performance do dia
        perf = await self.tools["performance_calculator"].execute(
            corretor_id,
            periodo="dia"
        )
        
        # Análise de demanda recente
        demanda = await self.tools["demand_aggregator"].execute(
            corretor_id,
            dias=7
        )
        
        # Análise de conversas
        conversas = await self.tools["conversation_analyzer"].execute(
            corretor_id,
            dias=7
        )
        
        # Gera insights
        insights = self._extrair_insights(demanda, conversas, perf)
        
        return {
            "periodo": hoje.strftime("%Y-%m-%d"),
            "metricas": perf,
            "demanda": demanda,
            "conversas": conversas,
            "insights": insights,
            "acoes_recomendadas": self._gerar_acoes(insights)
        }
    
    async def gerar_relatorio_semanal(
        self, 
        corretor_id: str
    ) -> Dict[str, Any]:
        """
        Gera relatório semanal completo
        
        Returns:
            Relatório estruturado com análises profundas
        """
        # Performance da semana
        perf_semana = await self.tools["performance_calculator"].execute(
            corretor_id,
            periodo="semana"
        )
        
        # Performance da semana anterior (para comparação)
        # TODO: Implementar busca de período específico
        
        # Análise de funil
        funil = await self.tools["conversion_tracker"].execute(corretor_id)
        
        # Análise de demanda
        demanda = await self.tools["demand_aggregator"].execute(
            corretor_id,
            dias=7
        )
        
        # Análise de conversas
        conversas = await self.tools["conversation_analyzer"].execute(
            corretor_id,
            dias=7
        )
        
        # Gera insights profundos
        insights_principais = self._extrair_insights_principais(
            perf_semana,
            demanda,
            conversas,
            funil
        )
        
        return {
            "periodo": perf_semana["periodo"],
            "metricas": perf_semana,
            "funil": funil,
            "demanda": demanda,
            "conversas": conversas,
            "insights_principais": insights_principais,
            "destaques": self._identificar_destaques(perf_semana, funil),
            "areas_atencao": self._identificar_areas_atencao(perf_semana, funil),
            "oportunidades": self._identificar_oportunidades(demanda, conversas)
        }
    
    async def analisar_lead(
        self, 
        lead_id: str
    ) -> Dict[str, Any]:
        """
        Análise profunda de um lead específico
        
        Returns:
            Score atualizado, perfil, recomendações
        """
        scoring = await self.tools["lead_scorer"].execute(lead_id)
        
        # TODO: Adicionar análise de histórico, padrões de comportamento
        
        return scoring
    
    async def detectar_padroes(
        self, 
        corretor_id: str,
        dias: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Detecta padrões emergentes na demanda
        
        Returns:
            Lista de padrões detectados com relevância
        """
        demanda = await self.tools["demand_aggregator"].execute(
            corretor_id,
            dias=dias
        )
        
        padroes = []
        
        # Analisa características em alta
        for caracteristica in demanda.get("caracteristicas_populares", []):
            if caracteristica["percentual"] >= 50:  # Mais de 50% dos leads
                padroes.append({
                    "tipo": "caracteristica_alta_demanda",
                    "descricao": f"{caracteristica['percentual']}% dos leads buscam {caracteristica['caracteristica']}",
                    "relevancia": "alta",
                    "count": caracteristica["count"]
                })
        
        # Analisa bairros concentrados
        bairros = demanda.get("bairros_mais_buscados", [])
        if bairros:
            top_bairro = bairros[0]
            if top_bairro["count"] >= 5:  # Threshold de relevância
                padroes.append({
                    "tipo": "concentracao_bairro",
                    "descricao": f"{top_bairro['bairro']} concentra {top_bairro['count']} leads esta semana",
                    "relevancia": "media",
                    "bairro": top_bairro["bairro"],
                    "count": top_bairro["count"]
                })
        
        return padroes
    
    def _extrair_insights(
        self,
        demanda: Dict,
        conversas: Dict,
        performance: Dict
    ) -> List[str]:
        """Extrai insights acionáveis dos dados"""
        insights = []
        
        # Insight de demanda
        if demanda.get("caracteristicas_populares"):
            top_caract = demanda["caracteristicas_populares"][0]
            insights.append(
                f"{top_caract['percentual']}% dos leads buscam {top_caract['caracteristica']}"
            )
        
        # Insight de horários
        if conversas.get("horarios_maior_engajamento"):
            horarios = ", ".join(conversas["horarios_maior_engajamento"])
            insights.append(
                f"Mensagens entre {horarios} têm maior taxa de resposta"
            )
        
        # Insight de performance
        if performance.get("leads_novos", 0) > 0:
            insights.append(
                f"{performance['leads_novos']} novos leads hoje"
            )
        
        return insights
    
    def _gerar_acoes(self, insights: List[str]) -> List[str]:
        """Gera ações recomendadas baseadas nos insights"""
        # TODO: Lógica mais sofisticada de recomendação
        return [
            "Priorizar leads com características de alta demanda",
            "Concentrar envios de mensagens nos horários de maior engajamento"
        ]
    
    def _extrair_insights_principais(
        self,
        performance: Dict,
        demanda: Dict,
        conversas: Dict,
        funil: Dict
    ) -> List[Dict[str, Any]]:
        """Extrai os 3-5 insights mais importantes da semana"""
        insights = []
        
        # TODO: Implementar lógica de priorização de insights
        
        return insights
    
    def _identificar_destaques(
        self,
        performance: Dict,
        funil: Dict
    ) -> List[str]:
        """Identifica pontos positivos da semana"""
        destaques = []
        
        # TODO: Implementar detecção de destaques
        
        return destaques
    
    def _identificar_areas_atencao(
        self,
        performance: Dict,
        funil: Dict
    ) -> List[str]:
        """Identifica áreas que precisam de atenção"""
        areas = []
        
        # TODO: Implementar detecção de gargalos
        
        return areas
    
    def _identificar_oportunidades(
        self,
        demanda: Dict,
        conversas: Dict
    ) -> List[str]:
        """Identifica oportunidades de mercado"""
        oportunidades = []
        
        # TODO: Implementar detecção de oportunidades
        
        return oportunidades
