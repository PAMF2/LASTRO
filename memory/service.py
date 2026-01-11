"""
Sistema de Memória - Gerencia dados persistentes de corretores e leads
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import redis
import json
from models import Corretor, Lead, Evento


class MemoryService:
    """
    Gerencia a memória persistente do sistema
    
    Usa Redis para cache rápido e PostgreSQL para persistência
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        db_session=None  # SQLAlchemy session
    ):
        self.redis = redis_client
        self.db = db_session
        self._cache = {}  # Cache em memória quando Redis não disponível
    
    # ==================== CORRETORES ====================
    
    async def get_corretor(self, corretor_id: str) -> Optional[Corretor]:
        """Busca corretor por ID"""
        # Tenta cache primeiro
        cache_key = f"corretor:{corretor_id}"
        
        if self.redis:
            cached = self.redis.get(cache_key)
            if cached:
                return Corretor.parse_raw(cached)
        elif cache_key in self._cache:
            return self._cache[cache_key]
        
        # TODO: Buscar do banco de dados
        # corretor = self.db.query(CorretorModel).filter_by(id=corretor_id).first()
        
        # Mock temporário
        return None
    
    async def save_corretor(self, corretor: Corretor) -> bool:
        """Salva corretor"""
        # Salva no cache
        cache_key = f"corretor:{corretor.id}"
        self.redis.setex(
            cache_key,
            3600,  # 1 hora
            corretor.json()
        )
        
        # TODO: Salvar no banco de dados
        
        return True
    
    async def list_corretores_ativos(self) -> List[Corretor]:
        """Lista todos os corretores ativos"""
        # TODO: Buscar do banco de dados
        return []
    
    # ==================== LEADS ====================
    
    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Busca lead por ID"""
        cache_key = f"lead:{lead_id}"
        cached = self.redis.get(cache_key)
        
        if cached:
            return Lead.parse_raw(cached)
        
        # TODO: Buscar do banco
        return None
    
    async def save_lead(self, lead: Lead) -> bool:
        """Salva lead"""
        cache_key = f"lead:{lead.id}"
        self.redis.setex(
            cache_key,
            7200,  # 2 horas
            lead.json()
        )
        
        # TODO: Salvar no banco
        return True
    
    async def get_leads_by_corretor(
        self, 
        corretor_id: str
    ) -> List[Lead]:
        """Busca todos os leads de um corretor"""
        # TODO: Buscar do banco com filtro
        # leads = self.db.query(LeadModel).filter_by(corretor_id=corretor_id).all()
        
        return []
    
    async def update_lead_score(
        self, 
        lead_id: str, 
        novo_score: int,
        fatores: List[str]
    ) -> bool:
        """Atualiza score de um lead"""
        lead = await self.get_lead(lead_id)
        if not lead:
            return False
        
        lead.score = novo_score
        lead.score_fatores = fatores
        
        return await self.save_lead(lead)
    
    # ==================== EVENTOS ====================
    
    async def save_evento(self, evento: Evento) -> bool:
        """Salva evento detectado"""
        cache_key = f"evento:{evento.id}"
        self.redis.setex(
            cache_key,
            86400,  # 24 horas
            evento.json()
        )
        
        # TODO: Salvar no banco
        return True
    
    async def get_eventos_pendentes(
        self, 
        corretor_id: str
    ) -> List[Evento]:
        """Busca eventos não processados de um corretor"""
        # TODO: Buscar do banco
        return []
    
    async def marcar_evento_processado(self, evento_id: str) -> bool:
        """Marca evento como processado"""
        evento = await self.get_evento(evento_id)
        if not evento:
            return False
        
        evento.processado = True
        await self.save_evento(evento)
        return True
    
    async def get_evento(self, evento_id: str) -> Optional[Evento]:
        """Busca evento por ID"""
        cache_key = f"evento:{evento_id}"
        cached = self.redis.get(cache_key)
        
        if cached:
            return Evento.parse_raw(cached)
        
        return None
    
    # ==================== HISTÓRICO ====================
    
    async def adicionar_interacao(
        self,
        lead_id: str,
        interacao: Dict[str, Any]
    ) -> bool:
        """Adiciona interação ao histórico do lead"""
        lead = await self.get_lead(lead_id)
        if not lead:
            return False
        
        # TODO: Converter dict para Interacao model
        # lead.interacoes.append(interacao)
        lead.data_ultima_interacao = datetime.utcnow()
        
        return await self.save_lead(lead)
    
    # ==================== MÉTRICAS ====================
    
    async def get_metricas_periodo(
        self,
        corretor_id: str,
        data_inicio: datetime,
        data_fim: datetime
    ) -> Dict[str, Any]:
        """Busca métricas de um período"""
        # TODO: Consultar banco com agregações
        return {
            "leads_novos": 0,
            "conversas": 0,
            "visitas": 0,
            "propostas": 0,
            "fechamentos": 0
        }
    
    # ==================== CACHE ====================
    
    def invalidar_cache_corretor(self, corretor_id: str):
        """Invalida cache do corretor"""
        cache_key = f"corretor:{corretor_id}"
        self.redis.delete(cache_key)
    
    def invalidar_cache_lead(self, lead_id: str):
        """Invalida cache do lead"""
        cache_key = f"lead:{lead_id}"
        self.redis.delete(cache_key)
