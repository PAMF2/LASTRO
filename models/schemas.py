from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    """Status possíveis de um lead"""
    NOVO = "novo"
    CONTATADO = "contatado"
    EM_NEGOCIACAO = "em_negociacao"
    VISITA_AGENDADA = "visita_agendada"
    PROPOSTA_ENVIADA = "proposta_enviada"
    FECHADO = "fechado"
    PERDIDO = "perdido"


class LeadUrgencia(str, Enum):
    """Nível de urgência do lead"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class InteracaoTipo(str, Enum):
    """Tipos de interação com o lead"""
    MENSAGEM_RECEBIDA = "mensagem_recebida"
    MENSAGEM_ENVIADA = "mensagem_enviada"
    LIGACAO = "ligacao"
    VISITA = "visita"
    PROPOSTA = "proposta"
    EMAIL = "email"


class Sentimento(str, Enum):
    """Sentimento detectado na interação"""
    INTERESSADO = "interessado"
    MUITO_INTERESSADO = "muito_interessado"
    HESITANTE = "hesitante"
    FRIO = "frio"
    NEGATIVO = "negativo"


class Interacao(BaseModel):
    """Interação com o lead"""
    data: datetime
    tipo: InteracaoTipo
    conteudo: str
    sentimento: Optional[Sentimento] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BuscaImovel(BaseModel):
    """Preferências de busca do lead"""
    bairros: List[str] = Field(default_factory=list)
    tipo: Optional[str] = None  # apartamento, casa, cobertura
    quartos_min: Optional[int] = None
    quartos_max: Optional[int] = None
    preco_min: Optional[float] = None
    preco_max: Optional[float] = None
    caracteristicas: List[str] = Field(default_factory=list)  # varanda, vaga, pet
    urgencia: Optional[str] = None
    financiamento: bool = False


class Lead(BaseModel):
    """Modelo de um lead"""
    id: str
    nome: str
    telefone: str
    email: Optional[str] = None
    origem: str  # zap_imoveis, vivareal, olx, indicacao
    corretor_id: str
    
    data_primeiro_contato: datetime
    data_ultima_interacao: Optional[datetime] = None
    
    busca: BuscaImovel = Field(default_factory=BuscaImovel)
    interacoes: List[Interacao] = Field(default_factory=list)
    
    score: int = 0  # 0-10
    score_fatores: List[str] = Field(default_factory=list)
    
    status: LeadStatus = LeadStatus.NOVO
    proximo_passo: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


class CorretorPreferencias(BaseModel):
    """Preferências do corretor"""
    frequencia_alertas: str = "media"  # baixa, media, alta
    horario_inicio: str = "08:00"
    horario_fim: str = "21:00"
    resumo_diario: bool = True
    resumo_semanal: bool = True
    max_mensagens_dia: int = 5


class CorretorAtuacao(BaseModel):
    """Área de atuação do corretor"""
    bairros: List[str] = Field(default_factory=list)
    tipos: List[str] = Field(default_factory=list)  # apartamento, casa, cobertura
    faixa_preco_min: Optional[float] = None
    faixa_preco_max: Optional[float] = None


class CorretorMetricas(BaseModel):
    """Métricas do corretor"""
    periodo_inicio: datetime
    periodo_fim: datetime
    conversas: int = 0
    visitas_agendadas: int = 0
    propostas: int = 0
    fechamentos: int = 0
    taxa_resposta: float = 0.0
    tempo_medio_resposta: str = "0h"
    leads_novos: int = 0
    leads_perdidos: int = 0


class Corretor(BaseModel):
    """Modelo de um corretor"""
    id: str
    nome: str
    telefone: str
    email: Optional[str] = None
    imobiliaria: Optional[str] = None
    creci: Optional[str] = None
    
    atuacao: CorretorAtuacao = Field(default_factory=CorretorAtuacao)
    preferencias: CorretorPreferencias = Field(default_factory=CorretorPreferencias)
    
    metricas_semana_atual: Optional[CorretorMetricas] = None
    
    padroes_detectados: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    ativo: bool = True
    data_cadastro: datetime = Field(default_factory=datetime.utcnow)


class EventoTipo(str, Enum):
    """Tipos de eventos detectados"""
    NOVO_LEAD = "novo_lead"
    LEAD_SEM_RESPOSTA = "lead_sem_resposta"
    CLIENTE_URGENTE = "cliente_urgente"
    PADRAO_DETECTADO = "padrao_detectado"
    VISITA_PROXIMA = "visita_proxima"
    IMOVEL_MUDANCA_PRECO = "imovel_mudanca_preco"
    FOLLOW_UP_PENDENTE = "follow_up_pendente"


class EventoUrgencia(str, Enum):
    """Urgência do evento"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class Evento(BaseModel):
    """Evento detectado pelo Vigilante"""
    id: str
    tipo: EventoTipo
    urgencia: EventoUrgencia
    corretor_id: str
    lead_id: Optional[str] = None
    
    titulo: str
    descricao: str
    acao_recomendada: Optional[str] = None
    
    data_deteccao: datetime = Field(default_factory=datetime.utcnow)
    processado: bool = False
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True
