"""
Script de teste simples do Lastro.AI
Testa conexão com Google Gemini e funcionalidades básicas
"""
import asyncio
from datetime import datetime
from loguru import logger
import google.generativeai as genai
from config.settings import settings

logger.info("🚀 Iniciando Lastro.AI - Teste Básico")

# Configurar Google Gemini
genai.configure(api_key=settings.google_api_key)

async def testar_gemini():
    """Testa a conexão com o Google Gemini"""
    logger.info("Testando Google Gemini...")
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = """Você é o Vigilante da Lastro.AI, um assistente para corretores de imóveis.
        
Responda em uma linha: você está funcionando corretamente?"""
        
        response = model.generate_content(prompt)
        logger.success(f"✅ Gemini funcionando! Resposta: {response.text}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com Gemini: {e}")
        return False

async def testar_database():
    """Testa conexão com o banco de dados"""
    logger.info("Testando conexão com PostgreSQL...")
    
    try:
        from sqlalchemy import create_engine, text
        
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.success(f"✅ PostgreSQL conectado! Versão: {version[:50]}...")
        return True
        
    except Exception as e:
        logger.warning(f"⚠️ PostgreSQL não disponível: {e}")
        return False

async def simular_evento_novo_lead():
    """Simula detecção de um novo lead"""
    logger.info("\n📋 Simulando evento: Novo Lead")
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = """Você é o Conselheiro da Lastro.AI. Um novo lead chegou:

Nome: Maria Silva
Origem: ZAP Imóveis
Interesse: Apartamento 3 quartos em Pinheiros, orçamento 800k-1M
Mensagem: "Oi, vi o anúncio do apto de 3 quartos em Pinheiros. Ainda está disponível?"

Gere uma mensagem curta e direta (máximo 3 linhas) para alertar o corretor. 
Inclua sugestão de resposta.

REGRAS:
- Seja direto, sem "olá" ou "tudo bem"
- Use emoji 🔔 no início
- Inclua sugestão de resposta entre aspas"""
    
    response = model.generate_content(prompt)
    logger.info(f"\n💬 Mensagem gerada:\n{response.text}\n")

async def simular_analise_semanal():
    """Simula geração de resumo semanal"""
    logger.info("\n📊 Simulando: Resumo Semanal")
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = """Você é o Analista da Lastro.AI. Gere um resumo semanal curto baseado nestes dados:

Período: 6-12 jan 2026
- 15 leads novos
- 47 conversas totais
- 12 visitas agendadas
- 3 propostas enviadas
- 1 fechamento

Padrões detectados:
- 67% dos leads mencionaram "varanda"
- Horário de maior engajamento: 10h-12h e 19h-21h
- 5 leads sem resposta há 48h+

Gere um resumo com:
📊 Métricas principais
📈 Destaque positivo
📉 Ponto de atenção
💡 Um insight acionável

Máximo 6 linhas."""
    
    response = model.generate_content(prompt)
    logger.info(f"\n📋 Resumo gerado:\n{response.text}\n")

async def main():
    """Executa todos os testes"""
    logger.info("="*60)
    logger.info("LASTRO.AI - TESTE DE FUNCIONAMENTO")
    logger.info("="*60)
    
    # Teste 1: Gemini
    gemini_ok = await testar_gemini()
    
    # Teste 2: Database
    db_ok = await testar_database()
    
    if not gemini_ok:
        logger.error("\n❌ Sistema não pode iniciar sem Gemini configurado")
        return
    
    # Testes de funcionalidade
    await simular_evento_novo_lead()
    await simular_analise_semanal()
    
    logger.info("="*60)
    logger.success("✅ TODOS OS TESTES CONCLUÍDOS!")
    logger.info("="*60)
    
    logger.info("\n📝 Status dos componentes:")
    logger.info(f"  • Google Gemini: {'✅ OK' if gemini_ok else '❌ ERRO'}")
    logger.info(f"  • PostgreSQL: {'✅ OK' if db_ok else '⚠️ Não configurado'}")
    logger.info(f"  • Agentes: ⚠️ Framework Agno não instalado (modo demo)")
    
    logger.info("\n💡 Próximos passos:")
    if not db_ok:
        logger.info("  1. Criar banco: CREATE DATABASE lastro_ai;")
    logger.info("  2. Configurar Twilio para WhatsApp")
    logger.info("  3. Implementar framework Agno completo")
    logger.info("  4. Iniciar com corretor piloto")

if __name__ == "__main__":
    asyncio.run(main())
