# 🏛️ ADR-008: Fila Local Permanente de Telemetria e Política de Expurgo TTL (5 Dias)

> **Status:** Homologada em Produção  
> **Data de Homologação:** 16/09/2026 (Refinada em 19/09/2026)  
> **Projetos de Origem:** `solicita-apac`, `sentinel`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Sistemas de telemetria baseados unicamente em envio síncrono sofrem perda irrecuperável de métricas quando há falhas temporárias de conexão com o servidor em nuvem (quedas de DNS, hibernação do Render, instabilidades de rota ou erros transitórios HTTP 500/502).

Se os lotes não forem gravados localmente de forma persistente, as horas humanas economizadas e as glosas evitadas deixam de ser computadas no Dashboard executivo da diretoria. Por outro lado, armazenar eventos locais indefinidamente sem expurgo acumula arquivos gigantes que degradam o desempenho e consomem espaço desnecessário nas estações de trabalho.

---

## 2. Decisão Arquitetural
Adotar um motor de **Fila Offline Permanente com Ciclo de Vida Bi-Estágio (`PENDING` e `SENT`) e TTL de 5 Dias**:

```text
[ Processamento do Lote Concluído ]
                 │
                 ▼
[ Serializa Payload sem PII ] ──▶ [ Enfileira como 'PENDING' em logs/.sentinel_telemetry_queue.json ]
                 │
                 ▼
       Tenta Envio Online ao Sentinel
       POST /api/v1/sentinel/telemetry
        │                             │
        │ (Sucesso HTTP 200/201)      │ (Falha de Rede / HTTP 500)
        ▼                             ▼
Status: 'SENT'                Permanece: 'PENDING'
sent_at: <timestamp_utc>      tentativas: N + 1
        │                     ultimo_erro: "HTTP 500: ..."
        │                             │
        ▼                             ▼
Expurgo TTL (5 Dias)          Nunca expurgado até ser entregue!
Apaga eventos 'SENT'          Na próxima inicialização do app:
com mais de 5 dias corridos.  tentar_reenvio_pendentes() faz auto-flush.
```

### Regras de Implementação:
1. **Local Canônico do Arquivo de Fila:**
   - `DEFAULT_TELEMETRY_QUEUE_FILE = LOGS_DIR / ".sentinel_telemetry_queue.json"`.
   - Compatibilidade automática com arquivos legados localizados na raiz da aplicação.
2. **Auto-Flush na Inicialização e Pré-Envio:**
   - Toda vez que a aplicação é iniciada ou antes de despachar um novo lote, a função `tentar_reenvio_pendentes()` é acionada.
   - Ela atualiza o token de sessão caso o registro original tenha sido gerado em modo offline contingencial e descarrega a fila pendente.
3. **Política Estrita de TTL (Time-To-Live de 5 Dias):**
   - Apenas registros com status `SENT` há mais de **5 dias corridos** são elegíveis para exclusão.
   - Registros com status `PENDING` **JAMAIS** são expurgados por tempo decorrido, garantindo que mesmo após finais de semana ou pausas operacionais de feriados, nenhum laudo faturado seja esquecido.

---

## 3. Consequências e Benefícios
- **Tolerância a Falhas e Desconexão:** Operação ininterrupta mesmo sem conexão com o Sentinel Hub.
- **Auditoria Financeira 100% Precisa:** Zero perda de métricas de produtividade hospitalar.
- **Higienização Automática de Armazenamento:** A pasta `logs/` se mantém leve e organizada sem necessidade de intervenção humana.
