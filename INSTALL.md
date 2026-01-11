# Guia de Instalação e Uso - Lastro.AI

## Instalação

### 1. Pré-requisitos

- Python 3.10 ou superior
- Redis (para cache/memória)
- PostgreSQL (para persistência)
- Conta Twilio (para WhatsApp Business API)
- Chaves de API: OpenAI ou Anthropic

### 2. Clonar e configurar

```bash
cd lastro.ai

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar .env com suas credenciais
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Variáveis obrigatórias:**
- `GOOGLE_API_KEY` (Google Gemini)
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER`
- `DATABASE_URL`
- `REDIS_HOST`

### 4. Inicializar banco de dados

```bash
# TODO: Criar migrations com Alembic
# alembic upgrade head
```

### 5. Executar

```bash
python main.py
```

---

## Arquitetura do Sistema

### Os 4 Componentes Principais

```
┌─────────────────────────────────────────────┐
│           ORQUESTRADOR (Team Lead)          │
│    Coordena tudo e gerencia prioridades     │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
┌───────▼──┐ ┌───▼────┐ ┌──▼────────┐
│ VIGILANTE│ │ANALISTA│ │CONSELHEIRO│
│          │ │        │ │           │
│ Monitora │ │Insights│ │ Comunica  │
│ eventos  │ │ dados  │ │ corretor  │
└──────────┘ └────────┘ └───────────┘
```

### 1. Agente Vigilante
**O que faz:**
- Monitora WhatsApp a cada 5 minutos
- Detecta novos leads de portais
- Identifica leads sem resposta
- Verifica compromissos próximos
- Detecta mudanças em imóveis

**Ferramentas que usa:**
- WhatsAppMonitor
- PortalMonitor
- CalendarCheck
- LeadStatusCheck
- ImovelMonitor

### 2. Agente Analista
**O que faz:**
- Analisa conversas e extrai padrões
- Calcula métricas de performance
- Detecta tendências de demanda
- Gera insights quantificados
- Score de leads

**Ferramentas que usa:**
- ConversationAnalyzer
- DemandAggregator
- LeadScorer
- PerformanceCalculator
- ConversionTracker

### 3. Agente Conselheiro
**O que faz:**
- Transforma alertas em mensagens claras
- Envia notificações ao corretor
- Gera resumos diários e semanais
- Sugere mensagens para clientes
- Respeita timing e contexto

**Ferramentas que usa:**
- WhatsAppSender
- MessageComposer
- TimingOptimizer
- ContextLoader
- MessageTemplates

### 4. Orquestrador
**O que faz:**
- Coordena os 3 agentes
- Prioriza eventos por urgência
- Evita sobrecarga de mensagens
- Agrupa notificações
- Garante máximo valor com mínimo ruído

---

## Fluxos Principais

### Fluxo 1: Novo Lead

```
1. Portal envia webhook → Vigilante detecta
2. Vigilante classifica como urgência ALTA
3. Orquestrador decide: enviar imediato
4. Conselheiro compõe mensagem e envia ao corretor
5. Corretor recebe notificação em < 5min
```

### Fluxo 2: Lead sem Resposta

```
1. Vigilante detecta lead há 24h sem resposta
2. Vigilante verifica score do lead (8/10 - quente)
3. Orquestrador prioriza como urgência ALTA
4. Analista consulta contexto do lead
5. Conselheiro gera sugestão de mensagem
6. Corretor recebe alerta com mensagem pronta
```

### Fluxo 3: Resumo Semanal

```
1. Segunda-feira 7h: Scheduler dispara
2. Orquestrador solicita relatório ao Analista
3. Analista processa:
   - Performance da semana
   - Padrões de demanda
   - Análise de conversas
   - Funil de conversão
4. Conselheiro formata resumo estruturado
5. Corretor recebe relatório completo
```

---

## Configurações do Corretor

Cada corretor pode personalizar:

### Preferências de Comunicação
```python
preferencias = {
    "frequencia_alertas": "media",  # baixa, media, alta
    "horario_inicio": "08:00",
    "horario_fim": "21:00",
    "resumo_diario": True,
    "resumo_semanal": True,
    "max_mensagens_dia": 5
}
```

### Área de Atuação
```python
atuacao = {
    "bairros": ["Pinheiros", "Itaim", "Vila Madalena"],
    "tipos": ["apartamento", "cobertura"],
    "faixa_preco_min": 500000,
    "faixa_preco_max": 3000000
}
```

---

## Customização

### Adicionar Nova Ferramenta

1. Criar classe em `tools/`:

```python
from tools.base import BaseTool

class MinhaNovaFerramenta(BaseTool):
    """Descrição da ferramenta"""
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        # Implementar lógica
        return {"resultado": "dados"}
```

2. Registrar no agente apropriado:

```python
# Em agents/vigilante.py (por exemplo)
self.tools["minha_ferramenta"] = MinhaNovaFerramenta()
```

### Adicionar Novo Template de Mensagem

Editar `tools/communication.py`:

```python
TEMPLATES = {
    "meu_template": """🔔 {titulo}

{conteudo}

{call_to_action}"""
}
```

### Modificar Regras de Priorização

Editar `agents/orquestrador.py`, método `_priorizar_eventos()`.

---

## Monitoramento

### Logs

Logs são salvos em `logs/lastro_YYYY-MM-DD.log`

```bash
# Ver logs em tempo real
tail -f logs/lastro_$(date +%Y-%m-%d).log
```

### Métricas

TODO: Implementar dashboard de métricas

---

## Troubleshooting

### Erro: "Redis connection refused"
**Solução:** Verificar se Redis está rodando
```bash
redis-cli ping
# Deve retornar: PONG
```

### Erro: "Twilio authentication failed"
**Solução:** Verificar credenciais no `.env`

### Agente não está detectando eventos
**Solução:** 
1. Verificar se há corretores ativos no banco
2. Verificar logs para erros específicos
3. Testar manualmente: `python -c "from agents import Orquestrador; ..."`

---

## Roadmap

### Fase 1: MVP (Em desenvolvimento) ✅
- [x] Agente Vigilante básico
- [x] Agente Conselheiro com envio
- [x] Alertas de novo lead e lead sem resposta
- [ ] Integração real com WhatsApp
- [ ] Testes com 1 corretor piloto

### Fase 2: Inteligência
- [ ] Agente Analista completo
- [ ] Scoring de leads com ML
- [ ] Detecção de padrões avançada
- [ ] Resumo semanal automatizado
- [ ] 5-10 corretores piloto

### Fase 3: Escala
- [ ] Integração com portais (ZAP, Viva Real, OLX)
- [ ] Integração com CRMs populares
- [ ] Dashboard web para corretores
- [ ] Onboarding self-service
- [ ] Lançamento público

---

## Suporte

Em caso de dúvidas ou problemas:

- **Documentação completa:** `README.md`
- **Knowledge base:** `knowledge/`
- **Issues:** [Criar issue no repositório]

---

## Licença

Proprietário - Lastro.AI © 2026
