"""
Ferramentas de análise - usadas pelo Agente Analista
"""
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import Counter
from .base import BaseTool
from models import Lead, Sentimento, InteracaoTipo


class ConversationAnalyzer(BaseTool):
    """Analisa conversas para extrair insights e padrões"""
    
    def __init__(self, memory_service):
        super().__init__()
        self.memory = memory_service
    
    async def execute(
        self, 
        corretor_id: str, 
        dias: int = 7
    ) -> Dict[str, Any]:
        """
        Analisa conversas dos últimos X dias
        
        Returns:
            {
                "total_conversas": 47,
                "sentimento_geral": "positivo",
                "palavras_mais_mencionadas": {
                    "varanda": 12,
                    "financiamento": 8,
                    "pet": 6
                },
                "objecoes_comuns": [
                    {"objecao": "preço alto", "frequencia": 5},
                    {"objecao": "localização", "frequencia": 3}
                ],
                "horarios_maior_engajamento": ["10:00-12:00", "19:00-21:00"]
            }
        """
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        leads = await self.memory.get_leads_by_corretor(corretor_id)
        
        total_conversas = 0
        palavras = []
        sentimentos = []
        horarios_msg = []
        
        for lead in leads:
            for interacao in lead.interacoes:
                if interacao.data >= data_inicio:
                    total_conversas += 1
                    
                    if interacao.sentimento:
                        sentimentos.append(interacao.sentimento.value)
                    
                    # Extrai palavras-chave (simplificado)
                    palavras.extend(
                        interacao.conteudo.lower().split()
                    )
                    
                    horarios_msg.append(interacao.data.hour)
        
        # Conta palavras mais comuns (filtrar stopwords em produção)
        palavras_comuns = Counter(palavras).most_common(10)
        
        # Analisa sentimentos
        if sentimentos:
            sentimento_predominante = Counter(sentimentos).most_common(1)[0][0]
        else:
            sentimento_predominante = "neutro"
        
        # Analisa horários
        faixas_horario = self._agrupar_horarios(horarios_msg)
        
        return {
            "total_conversas": total_conversas,
            "sentimento_geral": sentimento_predominante,
            "palavras_mais_mencionadas": dict(palavras_comuns),
            "objecoes_comuns": [],  # TODO: NLP mais sofisticado
            "horarios_maior_engajamento": faixas_horario
        }
    
    def _agrupar_horarios(self, horarios: List[int]) -> List[str]:
        """Agrupa horários em faixas"""
        faixas = {
            "08:00-10:00": 0,
            "10:00-12:00": 0,
            "12:00-14:00": 0,
            "14:00-16:00": 0,
            "16:00-18:00": 0,
            "18:00-20:00": 0,
            "20:00-22:00": 0,
        }
        
        for hora in horarios:
            if 8 <= hora < 10:
                faixas["08:00-10:00"] += 1
            elif 10 <= hora < 12:
                faixas["10:00-12:00"] += 1
            elif 12 <= hora < 14:
                faixas["12:00-14:00"] += 1
            elif 14 <= hora < 16:
                faixas["14:00-16:00"] += 1
            elif 16 <= hora < 18:
                faixas["16:00-18:00"] += 1
            elif 18 <= hora < 20:
                faixas["18:00-20:00"] += 1
            elif 20 <= hora < 22:
                faixas["20:00-22:00"] += 1
        
        # Retorna top 2 faixas
        faixas_ordenadas = sorted(faixas.items(), key=lambda x: x[1], reverse=True)
        return [f[0] for f in faixas_ordenadas[:2] if f[1] > 0]


class DemandAggregator(BaseTool):
    """Agrega e analisa padrões de demanda dos leads"""
    
    def __init__(self, memory_service):
        super().__init__()
        self.memory = memory_service
    
    async def execute(
        self, 
        corretor_id: str, 
        dias: int = 7
    ) -> Dict[str, Any]:
        """
        Detecta padrões de demanda
        
        Returns:
            {
                "bairros_mais_buscados": [
                    {"bairro": "Pinheiros", "count": 12},
                    {"bairro": "Itaim", "count": 8}
                ],
                "caracteristicas_populares": [
                    {"caracteristica": "varanda", "count": 15, "percentual": 67},
                    {"caracteristica": "pet friendly", "count": 10, "percentual": 45}
                ],
                "faixa_preco_media": {
                    "min": 600000,
                    "max": 1200000,
                    "media": 900000
                },
                "tendencias": [
                    "Aumento de 40% na busca por imóveis com home office",
                    "Preferência crescente por varandas gourmet"
                ]
            }
        """
        data_inicio = datetime.utcnow() - timedelta(days=dias)
        leads = await self.memory.get_leads_by_corretor(corretor_id)
        
        # Filtrar leads recentes
        leads_recentes = [
            l for l in leads 
            if l.data_primeiro_contato >= data_inicio
        ]
        
        # Agregar bairros
        bairros = []
        caracteristicas = []
        precos = []
        
        for lead in leads_recentes:
            bairros.extend(lead.busca.bairros)
            caracteristicas.extend(lead.busca.caracteristicas)
            
            if lead.busca.preco_max:
                precos.append(lead.busca.preco_max)
        
        bairros_count = Counter(bairros).most_common(5)
        caract_count = Counter(caracteristicas).most_common(5)
        
        total_leads = len(leads_recentes)
        
        caracteristicas_com_pct = [
            {
                "caracteristica": c[0],
                "count": c[1],
                "percentual": int((c[1] / total_leads) * 100) if total_leads > 0 else 0
            }
            for c in caract_count
        ]
        
        return {
            "bairros_mais_buscados": [
                {"bairro": b[0], "count": b[1]} 
                for b in bairros_count
            ],
            "caracteristicas_populares": caracteristicas_com_pct,
            "faixa_preco_media": {
                "min": min(precos) if precos else 0,
                "max": max(precos) if precos else 0,
                "media": sum(precos) // len(precos) if precos else 0
            },
            "tendencias": []  # TODO: Análise temporal mais sofisticada
        }


class LeadScorer(BaseTool):
    """Calcula score de leads baseado em múltiplos fatores"""
    
    async def execute(self, lead_id: str) -> Dict[str, Any]:
        """
        Calcula e atualiza o score de um lead
        
        Returns:
            {
                "lead_id": "lead_abc123",
                "score_anterior": 5,
                "score_novo": 8,
                "fatores": [
                    {"fator": "Respondeu em < 1h", "peso": +2},
                    {"fator": "Orçamento claro", "peso": +1},
                    {"fator": "Mencionou urgência", "peso": +2}
                ]
            }
        """
        # TODO: Implementar lógica de scoring sofisticada
        # Fatores: tempo de resposta, especificidade, orçamento, sentimento, etc.
        return {
            "lead_id": lead_id,
            "score_anterior": 0,
            "score_novo": 5,
            "fatores": []
        }


class PerformanceCalculator(BaseTool):
    """Calcula métricas de performance do corretor"""
    
    def __init__(self, memory_service):
        super().__init__()
        self.memory = memory_service
    
    async def execute(
        self, 
        corretor_id: str, 
        periodo: str = "semana"  # dia, semana, mes
    ) -> Dict[str, Any]:
        """
        Calcula métricas do corretor
        
        Returns:
            {
                "periodo": "2026-01-06 a 2026-01-12",
                "leads_novos": 15,
                "conversas_totais": 47,
                "visitas_agendadas": 12,
                "propostas_enviadas": 3,
                "fechamentos": 1,
                "taxa_conversao_lead_visita": 0.80,
                "taxa_conversao_visita_proposta": 0.25,
                "taxa_conversao_proposta_fechamento": 0.33,
                "tempo_medio_resposta": "4h 20min",
                "comparacao_periodo_anterior": {
                    "leads_novos": "+20%",
                    "conversas": "+15%",
                    "fechamentos": "=0%"
                }
            }
        """
        # Define período
        agora = datetime.utcnow()
        if periodo == "dia":
            data_inicio = agora - timedelta(days=1)
        elif periodo == "semana":
            data_inicio = agora - timedelta(days=7)
        else:  # mes
            data_inicio = agora - timedelta(days=30)
        
        # Busca dados
        leads = await self.memory.get_leads_by_corretor(corretor_id)
        
        # Calcula métricas
        leads_periodo = [
            l for l in leads 
            if l.data_primeiro_contato >= data_inicio
        ]
        
        return {
            "periodo": f"{data_inicio.strftime('%Y-%m-%d')} a {agora.strftime('%Y-%m-%d')}",
            "leads_novos": len(leads_periodo),
            "conversas_totais": sum(len(l.interacoes) for l in leads_periodo),
            "visitas_agendadas": 0,  # TODO: integrar com calendar
            "propostas_enviadas": 0,  # TODO: detectar propostas
            "fechamentos": 0,  # TODO: detectar fechamentos
            "taxa_conversao_lead_visita": 0.0,
            "taxa_conversao_visita_proposta": 0.0,
            "taxa_conversao_proposta_fechamento": 0.0,
            "tempo_medio_resposta": "0h",
            "comparacao_periodo_anterior": {}
        }


class ConversionTracker(BaseTool):
    """Rastreia e analisa conversões no funil"""
    
    async def execute(self, corretor_id: str) -> Dict[str, Any]:
        """
        Analisa o funil de conversão
        
        Returns:
            {
                "funil": {
                    "leads": 100,
                    "contatados": 85,
                    "interessados": 60,
                    "visitas": 20,
                    "propostas": 8,
                    "fechamentos": 3
                },
                "gargalos": [
                    "Queda de 65% entre interessados e visitas - investigar objeções"
                ],
                "oportunidades": [
                    "Taxa de fechamento pós-proposta está acima da média (37%)"
                ]
            }
        """
        # TODO: Implementar análise de funil completa
        return {
            "funil": {},
            "gargalos": [],
            "oportunidades": []
        }
