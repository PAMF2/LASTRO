# Arquitetura Técnica - Lastro.AI

## Visão Geral

```
┌──────────────────────────────────────────────────────────────┐
│                        LASTRO.AI                             │
│                   Sistema Multi-Agente                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼──────────┐            ┌────────▼─────────┐
│  Framework Agno  │            │  Infrastructure  │
│                  │            │                  │
│ • Agents         │            │ • Redis (cache)  │
│ • Tools          │            │ • PostgreSQL     │
│ • Teams          │            │ • Twilio         │
│ • Workflows      │            │ • APScheduler    │
└──────────────────┘            └──────────────────┘
```

---

## Stack Tecnológico

### Core
- **Python 3.10+**: Linguagem principal
- **Agno Framework**: Orquestração de agentes de IA
- **OpenAI GPT-4**: Motor de IA principal
- **Pydantic**: Validação de dados e models

### Armazenamento
- **Redis**: Cache em memória, fila de mensagens
- **PostgreSQL**: Persistência de dados estruturados
- **SQLAlchemy**: ORM para banco de dados

### Comunicação
- **Twilio WhatsApp API**: Integração com WhatsApp
- **httpx/aiohttp**: Cliente HTTP assíncrono
- **webhooks**: Recebimento de eventos dos portais

### Agendamento e Tasks
- **APScheduler**: Agendamento de tarefas periódicas
- **Celery** (futuro): Processamento distribuído

### Observabilidade
- **Loguru**: Logging estruturado
- **Sentry** (opcional): Monitoramento de erros

---

## Arquitetura de Dados

### Modelo de Dados Conceitual

```
┌──────────────┐       ┌──────────────┐
│   Corretor   │◄─────►│    Lead      │
│              │ 1:N   │              │
│ • ID         │       │ • ID         │
│ • Nome       │       │ • Nome       │
│ • Telefone   │       │ • Score      │
│ • Preferênc. │       │ • Status     │
└──────┬───────┘       └──────┬───────┘
       │                      │
       │                      │
       │                      ▼
       │               ┌──────────────┐
       │               │  Interação   │
       │               │              │
       │               │ • Data       │
       │               │ • Tipo       │
       │               │ • Conteúdo   │
       │               └──────────────┘
       │
       ▼
┌──────────────┐
│    Evento    │
│              │
│ • Tipo       │
│ • Urgência   │
│ • Ação       │
└──────────────┘
```

### Schema Redis (Cache)

```
Padrões de chave:

corretor:{id}               → Dados do corretor (TTL: 1h)
lead:{id}                   → Dados do lead (TTL: 2h)
evento:{id}                 → Evento detectado (TTL: 24h)
fila_agrupamento:{corretor} → Lista de eventos agrupados
mensagens_dia:{corretor}_{data} → Contador de mensagens

Estruturas:
- String: JSON serializado do modelo Pydantic
- List: Filas de eventos/mensagens
- Hash: Contadores e flags
```

### Schema PostgreSQL

```sql
-- Tabela de Corretores
CREATE TABLE corretores (
    id VARCHAR(50) PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(200),
    imobiliaria VARCHAR(200),
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT NOW(),
    preferencias JSONB,
    atuacao JSONB,
    metadata JSONB
);

-- Tabela de Leads
CREATE TABLE leads (
    id VARCHAR(50) PRIMARY KEY,
    corretor_id VARCHAR(50) REFERENCES corretores(id),
    nome VARCHAR(200) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(200),
    origem VARCHAR(50),
    data_primeiro_contato TIMESTAMP,
    data_ultima_interacao TIMESTAMP,
    score INTEGER DEFAULT 0,
    status VARCHAR(50),
    busca JSONB,
    metadata JSONB
);

-- Tabela de Interações
CREATE TABLE interacoes (
    id SERIAL PRIMARY KEY,
    lead_id VARCHAR(50) REFERENCES leads(id),
    data TIMESTAMP DEFAULT NOW(),
    tipo VARCHAR(50),
    conteudo TEXT,
    sentimento VARCHAR(50),
    metadata JSONB
);

-- Tabela de Eventos
CREATE TABLE eventos (
    id VARCHAR(50) PRIMARY KEY,
    tipo VARCHAR(50),
    urgencia VARCHAR(20),
    corretor_id VARCHAR(50) REFERENCES corretores(id),
    lead_id VARCHAR(50) REFERENCES leads(id),
    titulo VARCHAR(500),
    descricao TEXT,
    acao_recomendada TEXT,
    data_deteccao TIMESTAMP DEFAULT NOW(),
    processado BOOLEAN DEFAULT FALSE,
    metadata JSONB
);

-- Índices
CREATE INDEX idx_leads_corretor ON leads(corretor_id);
CREATE INDEX idx_leads_score ON leads(score DESC);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_interacoes_lead ON interacoes(lead_id);
CREATE INDEX idx_eventos_corretor ON eventos(corretor_id);
CREATE INDEX idx_eventos_processado ON eventos(processado);
```

---

## Fluxo de Dados

### 1. Ingestão de Dados

```
┌─────────────┐
│   Portais   │ (ZAP, Viva Real, OLX)
└──────┬──────┘
       │ webhook
       ▼
┌─────────────┐
│  API Server │ (FastAPI - futuro)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Vigilante  │ detecta novo lead
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Orquestrador│ processa
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Conselheiro │ notifica corretor
└─────────────┘
```

### 2. Processamento de Eventos

```
Vigilante detecta evento
        ↓
Evento salvo em Redis/PostgreSQL
        ↓
Orquestrador lê fila de eventos
        ↓
Aplica regras de priorização
        ↓
    ┌───┴───┐
    │       │
Enviar    Agendar
agora     para depois
    │       │
    └───┬───┘
        ↓
Conselheiro executa
```

### 3. Ciclo de Análise

```
Scheduler dispara (diário/semanal)
        ↓
Analista busca dados do período
        ↓
Processa com ferramentas:
  • ConversationAnalyzer
  • DemandAggregator
  • PerformanceCalculator
        ↓
Gera insights estruturados
        ↓
Conselheiro formata e envia
```

---

## Escalabilidade

### Estratégias de Scale

#### Horizontal (curto prazo)
```
┌─────────────┐
│  Load       │
│  Balancer   │
└──────┬──────┘
       │
    ┌──┴──┐
    │     │
┌───▼──┐ ┌▼────┐
│Inst 1│ │Inst2│
│Redis │ │Redis│
└──┬───┘ └─┬───┘
   │       │
   └───┬───┘
       ▼
┌─────────────┐
│ PostgreSQL  │
│  (Master)   │
└─────────────┘
```

#### Vertical (médio prazo)
- Redis Cluster para distribuição
- PostgreSQL com replicas read-only
- Celery workers para processamento distribuído

#### Arquitetura (longo prazo)
```
┌─────────────────┐
│   API Gateway   │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│Agentes│ │Workers│
│Service│ │Service│
└───┬───┘ └───┬───┘
    │         │
┌───▼─────────▼───┐
│  Message Queue  │
│  (RabbitMQ)     │
└─────────────────┘
```

---

## Performance

### Otimizações Implementadas

1. **Caching agressivo**
   - Corretores: TTL 1h
   - Leads: TTL 2h
   - Eventos: TTL 24h

2. **Queries otimizadas**
   - Índices em colunas frequentemente consultadas
   - Eager loading de relacionamentos

3. **Processamento assíncrono**
   - Todas operações I/O são async
   - Uso de asyncio para paralelismo

### Métricas Esperadas (MVP)

- **Latência de detecção**: < 30s
- **Latência de notificação**: < 5min
- **Throughput**: 100 eventos/min por instância
- **Memória**: ~500MB por instância
- **CPU**: ~30% em operação normal

---

## Segurança

### Dados Sensíveis

- Credenciais em `.env` (nunca commitadas)
- Tokens de API criptografados em banco
- Números de telefone ofuscados em logs

### Compliance

- LGPD: Dados pessoais com consentimento explícito
- Retenção: 30 dias de logs, 2 anos de dados operacionais
- Direito ao esquecimento: Endpoint de deleção de dados

### Rate Limiting

```python
# Por corretor
MAX_MENSAGENS_DIA = 5  # configurável

# APIs externas
TWILIO_RATE_LIMIT = 100  # por segundo
OPENAI_RATE_LIMIT = 3000  # por minuto
```

---

## Testes

### Estratégia de Testes

```
tests/
├── unit/               # Testes unitários
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_models.py
├── integration/        # Testes de integração
│   ├── test_workflows.py
│   └── test_memory.py
└── e2e/               # Testes end-to-end
    └── test_scenarios.py
```

### Cobertura Esperada

- Unit tests: > 80%
- Integration tests: > 60%
- E2E tests: Cenários críticos (novo lead, follow-up, resumo)

---

## Deployment

### Ambiente de Produção

```yaml
# docker-compose.yml
version: '3.8'

services:
  lastro:
    build: .
    environment:
      - ENVIRONMENT=production
    depends_on:
      - redis
      - postgres
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pytest
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: docker build -t lastro:latest .
      - run: docker push lastro:latest
      - run: kubectl apply -f k8s/
```

---

## Monitoramento

### Métricas Chave

- **Operacionais:**
  - Eventos detectados/hora
  - Mensagens enviadas/dia
  - Latência média de processamento

- **Negócio:**
  - Taxa de conversão lead → visita
  - Tempo médio de primeira resposta
  - Score médio de leads

- **Sistema:**
  - CPU/memória
  - Erros/min
  - Uptime

### Alertas

```python
# Exemplos de alertas
- Latência > 5min: WARNING
- Taxa de erro > 5%: CRITICAL
- Redis down: CRITICAL
- Fila de eventos > 1000: WARNING
```

---

## Roadmap Técnico

### Q1 2026
- [ ] Implementar banco de dados PostgreSQL completo
- [ ] Integração real com Twilio WhatsApp
- [ ] Webhooks dos portais
- [ ] Dashboard básico de métricas

### Q2 2026
- [ ] ML para scoring de leads
- [ ] Análise de sentimento avançada
- [ ] Celery para processamento distribuído
- [ ] API REST pública

### Q3 2026
- [ ] Kubernetes deployment
- [ ] Multi-tenant architecture
- [ ] Webhooks customizáveis
- [ ] Integrações com CRMs populares

---

Documento mantido por: Equipe Lastro.AI  
Última atualização: 2026-01-11
