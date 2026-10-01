# 🏛️ ADR-011: Pre-Check de Integridade Cadastral, Caches em Memória e Telemetria de Triagem

> **Status:** Homologada em Produção  
> **Data de Homologação:** 19/09/2026  
> **Projetos de Origem:** `solicita-apac`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Em sistemas de automação de faturamento (como o APACnet), tentar gravar laudos diretamente sem validação prévia de integridade acarreta riscos severos:
1. Pacientes podem conter divergências cadastrais (nome grafado incorretamente, CPF inválido, mãe divergente);
2. Pacientes podem violar regras de periodicidade SUS (ex: consulta de glaucoma solicitada com menos de 90 dias do último acompanhamento, gerando glosa irreversível);
3. Podem existir solicitações pendentes de autorização na regulação estadual (ex: lançadas no dia anterior manualmente), gerando laudos duplicados indesejados;
4. Realizar consultas repetidas de histórico ao portal hospitalar para cada validação sobrecarrega a rede e torna a automação lenta.

---

## 2. Decisão Arquitetural
Dividir a execução em duas etapas estritamente segregadas: **Fase 1: Pre-Check de Integridade** e **Fase 2: Injeção de Produção**, acelerada por **Caches em Memória $O(1)$**:

```text
[ Planilha de Pacientes ]
           │
           ▼
[ ETAPA 1: PRE-CHECK DE INTEGRIDADE & AUDITORIA ]
  ├── Validação de CPF (Módulo 11) e Nome Estrito
  ├── Consulta ao Monitor de Pendências (1 GET leve em lote com cache em memória)
  ├── Checagem das 6 Regras de Ouro de Periodicidade SUS (com cache de histórico por lote)
  └── Painel Consolidado de Triagem:
      • Total Aptos para Envio
      • Bloqueios SUS de Periodicidade (Glosas Prevenidas)
      • Alertas Clínicos Preventivos
      • Inconsistências Cadastrais
           │
           ▼
   Prompt de Decisão do Operador:
   [P = Prosseguir com Aptos | C = Cancelar Lote | V = Verificar Novamente]
           │
           ├─▶ Se Cancelar ou 0 Aptos:
           │   Despacha Telemetria de Triagem ao Sentinel (horas de auditoria salvas)
           │
           ▼ (Se 'P')
[ ETAPA 2: GRAVAÇÃO / INJEÇÃO REAL ]
  Apenas pacientes rigorosamente aprovados na Etapa 1 são despachados.
```

### Regras de Otimização com Caches em Memória:
1. **Cache de Histórico por Lote (`lote_historico_cache`):**
   - Durante a avaliação do lote, o histórico de APACs autorizadas de um paciente é consultado uma única vez e armazenado em memória na sessão;
   - Todas as verificações de periodicidade de regras cruzadas consultam o cache em $O(1)$.
2. **Cache em Lote do Monitor de Pendências (`cache_pendentes_monitor`):**
   - Um único GET leve (~36 KB / 0.3s) é feito no endpoint de acompanhamento;
   - As solicitações pendentes são parseadas e indexadas em memória por nome e data, bloqueando imediatamente duplicidades sem consultar o portal individualmente.
3. **Telemetria de Triagem para Lotes Sem Laudos Aprovados:**
   - Mesmo que 100% dos pacientes sejam bloqueados por duplicidade ou que o operador cancele o lote para ajustes na recepção, a telemetria é despachada ao Sentinel computando o tempo humano de auditoria e as glosas evitadas.

---

## 3. Consequências e Benefícios
- **Zero Glosas de Periodicidade:** Nenhuma solicitação inválida avança para o portal governamental.
- **Performance Extrema:** 11 pacientes checados e auditados em apenas 21.4 segundos.
- **Rastreabilidade Total de Produtividade:** O valor gerado pela auditoria preventiva é 100% refletido nos Big Numbers do Dashboard executivo.
