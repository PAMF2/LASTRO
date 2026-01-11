"""
Lastro.AI - Sistema de assistência inteligente para corretores de imóveis

Ponto de entrada principal do sistema
"""
import asyncio
from datetime import datetime, time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
import redis
from config.settings import settings
from memory import MemoryService
from agents import Orquestrador


class LastroAI:
    """
    Aplicação principal do Lastro.AI
    
    Gerencia o ciclo de vida dos agentes e agendamento de tarefas
    """
    
    def __init__(self):
        logger.info("Inicializando Lastro.AI...")
        
        # Configurar logging
        self._setup_logging()
        
        # Inicializar Redis (opcional)
        self.redis_client = None
        if settings.redis_host:
            try:
                self.redis_client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info("Redis conectado")
            except Exception as e:
                logger.warning(f"Redis não disponível, usando cache em memória: {e}")
        else:
            logger.info("Redis não configurado, usando cache em memória")
        
        # Inicializar serviço de memória
        self.memory = MemoryService(self.redis_client)
        logger.info("Memory service inicializado")
        
        # Inicializar Twilio (WhatsApp)
        # TODO: Implementar client Twilio real
        self.twilio_client = None
        
        # Inicializar Orquestrador
        self.orquestrador = Orquestrador(
            memory_service=self.memory,
            twilio_client=self.twilio_client
        )
        logger.info("Orquestrador inicializado")
        
        # Scheduler para tarefas periódicas
        self.scheduler = AsyncIOScheduler()
        self._setup_scheduled_tasks()
    
    def _setup_logging(self):
        """Configura sistema de logging"""
        logger.add(
            "logs/lastro_{time}.log",
            rotation="1 day",
            retention="30 days",
            level=settings.log_level
        )
    
    def _setup_scheduled_tasks(self):
        """Configura tarefas agendadas"""
        
        # Vigilante: Monitoramento a cada 5 minutos
        self.scheduler.add_job(
            self._executar_vigilante,
            CronTrigger(minute=f"*/{settings.vigilante_check_interval_minutes}"),
            id="vigilante_monitor",
            name="Monitoramento do Vigilante"
        )
        
        # Resumo da manhã: 7h
        self.scheduler.add_job(
            self._enviar_resumos_manha,
            CronTrigger(hour=7, minute=0),
            id="resumo_manha",
            name="Resumo da manhã"
        )
        
        # Resumo da noite: 20h
        self.scheduler.add_job(
            self._enviar_resumos_noite,
            CronTrigger(hour=20, minute=0),
            id="resumo_noite",
            name="Resumo da noite"
        )
        
        # Resumo semanal: Segunda 7h
        self.scheduler.add_job(
            self._enviar_resumos_semanais,
            CronTrigger(day_of_week="mon", hour=7, minute=0),
            id="resumo_semanal",
            name="Resumo semanal"
        )
        
        # Detecção de padrões: Diariamente às 6h
        self.scheduler.add_job(
            self._detectar_padroes,
            CronTrigger(hour=6, minute=0),
            id="detectar_padroes",
            name="Detecção de padrões"
        )
        
        logger.info("Tarefas agendadas configuradas")
    
    async def _executar_vigilante(self):
        """Executa ciclo de monitoramento do Vigilante"""
        logger.info("Iniciando ciclo do Vigilante")
        
        try:
            # Busca todos os corretores ativos
            corretores = await self.memory.list_corretores_ativos()
            
            for corretor in corretores:
                try:
                    resultado = await self.orquestrador.processar_corretor(
                        corretor.id
                    )
                    
                    logger.info(
                        f"Corretor {corretor.nome}: "
                        f"{resultado['eventos_detectados']} eventos, "
                        f"{resultado['mensagens_enviadas']} mensagens enviadas"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Erro ao processar corretor {corretor.id}: {e}"
                    )
        
        except Exception as e:
            logger.error(f"Erro no ciclo do Vigilante: {e}")
    
    async def _enviar_resumos_manha(self):
        """Envia resumos matinais"""
        logger.info("Enviando resumos da manhã")
        
        try:
            corretores = await self.memory.list_corretores_ativos()
            
            for corretor in corretores:
                if not corretor.preferencias.resumo_diario:
                    continue
                
                try:
                    await self.orquestrador.gerar_resumo_diario(
                        corretor.id,
                        horario="manha"
                    )
                    logger.info(f"Resumo enviado para {corretor.nome}")
                    
                except Exception as e:
                    logger.error(
                        f"Erro ao enviar resumo para {corretor.id}: {e}"
                    )
        
        except Exception as e:
            logger.error(f"Erro ao enviar resumos da manhã: {e}")
    
    async def _enviar_resumos_noite(self):
        """Envia resumos noturnos"""
        logger.info("Enviando resumos da noite")
        
        try:
            corretores = await self.memory.list_corretores_ativos()
            
            for corretor in corretores:
                if not corretor.preferencias.resumo_diario:
                    continue
                
                try:
                    await self.orquestrador.gerar_resumo_diario(
                        corretor.id,
                        horario="noite"
                    )
                    logger.info(f"Resumo enviado para {corretor.nome}")
                    
                except Exception as e:
                    logger.error(
                        f"Erro ao enviar resumo para {corretor.id}: {e}"
                    )
        
        except Exception as e:
            logger.error(f"Erro ao enviar resumos da noite: {e}")
    
    async def _enviar_resumos_semanais(self):
        """Envia resumos semanais"""
        logger.info("Enviando resumos semanais")
        
        try:
            corretores = await self.memory.list_corretores_ativos()
            
            for corretor in corretores:
                if not corretor.preferencias.resumo_semanal:
                    continue
                
                try:
                    await self.orquestrador.gerar_resumo_semanal(
                        corretor.id
                    )
                    logger.info(f"Resumo semanal enviado para {corretor.nome}")
                    
                except Exception as e:
                    logger.error(
                        f"Erro ao enviar resumo semanal para {corretor.id}: {e}"
                    )
        
        except Exception as e:
            logger.error(f"Erro ao enviar resumos semanais: {e}")
    
    async def _detectar_padroes(self):
        """Detecta e comunica padrões emergentes"""
        logger.info("Detectando padrões de demanda")
        
        try:
            corretores = await self.memory.list_corretores_ativos()
            
            for corretor in corretores:
                try:
                    padroes = await self.orquestrador.detectar_e_comunicar_padroes(
                        corretor.id
                    )
                    
                    if padroes:
                        logger.info(
                            f"Corretor {corretor.nome}: "
                            f"{len(padroes)} padrões comunicados"
                        )
                
                except Exception as e:
                    logger.error(
                        f"Erro ao detectar padrões para {corretor.id}: {e}"
                    )
        
        except Exception as e:
            logger.error(f"Erro na detecção de padrões: {e}")
    
    async def run(self):
        """Inicia o sistema"""
        logger.info("🚀 Lastro.AI iniciado!")
        
        # Inicia o scheduler
        self.scheduler.start()
        logger.info("Scheduler iniciado")
        
        # Mantém o processo rodando
        try:
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Encerrando Lastro.AI...")
            self.scheduler.shutdown()
            logger.info("✅ Lastro.AI encerrado")
    
    async def processar_mensagem_corretor(
        self,
        corretor_id: str,
        mensagem: str
    ) -> str:
        """
        Processa mensagem do corretor (interação via WhatsApp)
        
        Permite que o corretor faça perguntas ou solicite ações
        """
        logger.info(f"Mensagem do corretor {corretor_id}: {mensagem}")
        
        # TODO: Implementar processamento de linguagem natural
        # para entender comandos como:
        # - "quem são meus leads mais quentes?"
        # - "me dá uma mensagem pra mandar pro João"
        # - "como foi minha semana?"
        # - "tenho algum compromisso hoje?"
        
        return "Funcionalidade em desenvolvimento"


def main():
    """Função principal"""
    app = LastroAI()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
