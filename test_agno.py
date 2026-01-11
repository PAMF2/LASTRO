"""
Teste básico do Agno com Google Gemini
"""
from agno.agent import Agent
from agno.models.google import Gemini
from agno.os import AgentOS
from config.settings import settings

print("🚀 Testando Agno Framework com Google Gemini\n")

# Criar agente simples
agente_teste = Agent(
    name="Teste Lastro",
    model=Gemini(id="gemini-2.5-flash", api_key=settings.google_api_key),
    instructions="Você é um assistente para corretores de imóveis. Responda de forma breve e direta.",
    markdown=True,
)

# Criar AgentOS
agent_os = AgentOS(agents=[agente_teste])

# Obter app FastAPI
app = agent_os.get_app()

print("✅ Agno configurado com sucesso!")
print(f"✅ Agente criado: {agente_teste.name}")
print(f"✅ Modelo: Gemini 2.0 Flash")
print("\n" + "="*60)
print("Para iniciar o servidor FastAPI, execute:")
print("fastapi dev test_agno.py")
print("="*60)

if __name__ == "__main__":
    # Teste rápido de geração
    print("\n🧪 Teste de geração de resposta:\n")
    
    response = agente_teste.run("Qual a importância de responder um lead em até 5 minutos?")
    
    print("Resposta do agente:")
    print("-" * 60)
    print(response.content)
    print("-" * 60)
    
    print("\n✅ Teste concluído com sucesso!")
