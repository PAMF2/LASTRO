"""
Lastro.AI - Versão Demo Local
Demonstra a arquitetura sem APIs externas
"""
import asyncio
from datetime import datetime, timedelta
from loguru import logger
from typing import List, Dict, Any

logger.info("🚀 Lastro.AI - Demo Mode")

# Simulação de dados
class MockLead:
    def __init__(self, nome, score, horas_sem_resposta):
        self.nome = nome
        self.score = score
        self.horas_sem_resposta = horas_sem_resposta
        self.ultima_msg = "Tem financiamento disponível?"

class AgenteVigilanteDemo:
    """Versão demo do Vigilante"""
    
    def detectar_eventos(self) -> List[Dict[str, Any]]:
        """Simula detecção de eventos"""
        logger.info("🔍 Vigilante monitorando...")
        
        eventos = [
            {
                "tipo": "novo_lead",
                "urgencia": "alta",
                "dados": {
                    "nome": "Maria Silva",
                    "origem": "ZAP Imóveis",
                    "interesse": "3q Pinheiros, 800k-1M"
                }
            },
            {
                "tipo": "lead_sem_resposta",
                "urgencia": "alta",
                "dados": {
                    "nome": "João Santos",
                    "horas": 26,
                    "score": 9
                }
            }
        ]
        
        logger.success(f"✅ {len(eventos)} eventos detectados")
        return eventos

class AgenteAnalistaDemo:
    """Versão demo do Analista"""
    
    def analisar_semana(self) -> Dict[str, Any]:
        """Simula análise semanal"""
        logger.info("📊 Analista processando dados...")
        
        analise = {
            "leads_novos": 15,
            "conversas": 47,
            "visitas": 12,
            "propostas": 3,
            "padroes": [
                "67% dos leads mencionaram 'varanda'",
                "Horários 10h-12h e 19h-21h têm 2x mais engajamento"
            ]
        }
        
        logger.success("✅ Análise concluída")
        return analise

class AgenteConselheiroDemo:
    """Versão demo do Conselheiro"""
    
    def gerar_mensagem(self, evento: Dict) -> str:
        """Gera mensagem baseada no evento"""
        logger.info("💬 Conselheiro gerando mensagem...")
        
        if evento["tipo"] == "novo_lead":
            msg = f"""🔔 Novo lead: {evento['dados']['nome']}

{evento['dados']['interesse']}

💡 Responder em até 5min aumenta conversão em 9x

Sugestão:
"Oi {evento['dados']['nome'].split()[0]}! Vi seu interesse no 3q em Pinheiros. 
Esse apartamento tem exatamente o que você busca. 
Quando podemos conversar sobre as condições?"
"""
        
        elif evento["tipo"] == "lead_sem_resposta":
            msg = f"""⏰ {evento['dados']['nome']} sem resposta há {evento['dados']['horas']}h

Score: {evento['dados']['score']}/10 - Lead QUENTE

Sugestão:
"Oi {evento['dados']['nome'].split()[0]}! Ainda interessado no apartamento?
Tenho uma novidade: o proprietário aceitou negociar o valor.
Quer saber mais?"
"""
        
        return msg

class OrquestradorDemo:
    """Versão demo do Orquestrador"""
    
    def __init__(self):
        self.vigilante = AgenteVigilanteDemo()
        self.analista = AgenteAnalistaDemo()
        self.conselheiro = AgenteConselheiroDemo()
    
    async def ciclo_completo(self):
        """Executa um ciclo completo de processamento"""
        logger.info("\n" + "="*60)
        logger.info("ORQUESTRADOR: Iniciando ciclo de processamento")
        logger.info("="*60 + "\n")
        
        # 1. Vigilante detecta eventos
        eventos = self.vigilante.detectar_eventos()
        
        # 2. Orquestrador prioriza
        logger.info("\n🎯 Orquestrador priorizando eventos...")
        eventos_priorizados = sorted(
            eventos, 
            key=lambda x: 1 if x["urgencia"] == "alta" else 2
        )
        logger.success(f"✅ {len(eventos_priorizados)} eventos priorizados\n")
        
        # 3. Conselheiro gera mensagens
        logger.info("📤 Enviando alertas ao corretor:\n")
        for evento in eventos_priorizados[:2]:  # Max 2 por demo
            mensagem = self.conselheiro.gerar_mensagem(evento)
            print("─" * 60)
            print(mensagem)
            print("─" * 60 + "\n")
            await asyncio.sleep(1)
        
        # 4. Analista gera insights
        logger.info("\n📊 Gerando resumo semanal...\n")
        analise = self.analista.analisar_semana()
        
        print("─" * 60)
        print(f"""📊 Sua semana (6-12 jan):

{analise['leads_novos']} leads | {analise['conversas']} conversas | {analise['visitas']} visitas | {analise['propostas']} propostas

💡 Insights:
• {analise['padroes'][0]}
• {analise['padroes'][1]}

📈 Destaque: Conversões aumentaram 20%
📉 Atenção: 5 leads quentes sem follow-up
""")
        print("─" * 60 + "\n")

async def main():
    """Função principal"""
    logger.info("="*60)
    logger.info("LASTRO.AI - DEMONSTRAÇÃO DO SISTEMA")
    logger.info("Versão: MVP Demo (sem APIs externas)")
    logger.info("="*60 + "\n")
    
    orquestrador = OrquestradorDemo()
    await orquestrador.ciclo_completo()
    
    logger.info("="*60)
    logger.success("✅ DEMONSTRAÇÃO CONCLUÍDA!")
    logger.info("="*60 + "\n")
    
    logger.info("🎯 Arquitetura Demonstrada:")
    logger.info("  • Agente Vigilante: Detectou 2 eventos")
    logger.info("  • Agente Analista: Gerou insights quantificados")
    logger.info("  • Agente Conselheiro: Criou mensagens acionáveis")
    logger.info("  • Orquestrador: Coordenou todo o fluxo\n")
    
    logger.info("💡 Para ativar modo produção:")
    logger.info("  1. Configurar API do Google Gemini com cota adequada")
    logger.info("  2. Conectar PostgreSQL (CREATE DATABASE lastro_ai)")
    logger.info("  3. Adicionar credenciais Twilio WhatsApp")
    logger.info("  4. Configurar webhooks dos portais")

if __name__ == "__main__":
    asyncio.run(main())
