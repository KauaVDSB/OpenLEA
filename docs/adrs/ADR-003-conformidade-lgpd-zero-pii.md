# 🏛️ ADR-003: Conformidade LGPD Estrita, Mascaramento PII e Sanitização de Strings

> **Status:** Homologada em Produção  
> **Data de Homologação:** 10/09/2026 (Atualizada em 19/09/2026)  
> **Projetos de Origem:** `solicita-apac`, `sentinel`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Sistemas de saúde operam sob regulação estrita da Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018). Dados clínicos e identificadores como CPF, Cartão Nacional de Saúde (CNS), nome completo de pacientes e diagnósticos (CID-10) são classificados como dados sensíveis. O vazamento desses dados para logs em texto claro, arquivos versionados no GitHub ou plataformas cloud externas de telemetria acarretaria penalidades jurídicas graves.

Além disso, identificou-se em produção que mensagens longas de erro com dados de auditoria detalhados podem ultrapassar os limites de colunas relacionais comuns (`VARCHAR(255)`), provocando rollbacks e erros HTTP 500 no servidor de telemetria.

---

## 2. Decisão Arquitetural
Adotar um protocolo de conformidade em três camadas:

```text
1. Mascaramento em Camada Local (Logs & UI)
   ex: CPF: 114.***.***-28 | Paciente: MARIA H...

2. Telemetria Cloud Zero PII (ADR-003)
   Payload transmitido: { "lote_id": "...", "sucessos": 10, "inconsistencias": 1, "tempo_total": 21.4 }

3. Sanitização Defensiva de Tamanho de Strings (<= 250 chars)
   Truncamento preventivo client-side + truncamento defensivo server-side
```

### Regras de Implementação:
1. **Blindagem do Repositório (`.gitignore`):**
   - Bloquear arquivos `.xlsx`, `.csv`, `.pdf`, `.json`, `.db`, `.sqlite3`, `.env`, dumps e capturas de tela.
2. **Função Canônica de Mascaramento (`core/config.py`):**
   ```python
   def mascarar_cpf(cpf: str | int | float | None) -> str:
       limpo = "".join(filter(str.isdigit, str(cpf or "")))
       if len(limpo) == 11:
           return f"{limpo[:3]}.***.***-{limpo[-2:]}"
       return "***"
   ```
3. **Telemetria Agregada sem PII:**
   - O objeto `TelemetryPayload` transmitido ao Sentinel **NUNCA** recebe nomes de pacientes, CPFs ou prontuários.
   - Os erros são reportados de forma puramente tipificada (ex: `"Glosa de Periodicidade SUS"`, `"Nome divergente no portal"`).
4. **Sanitização de Tamanho de String ($\le 250$ caracteres):**
   - No cliente: `(motivo[:247] + "...") if len(motivo) > 250 else motivo`.
   - No servidor: `motivo=(erro.motivo or "Inconsistência")[:255]`.

---

## 3. Consequências e Benefícios
- **Conformidade Legal Plena:** Total aderência à LGPD e às diretrizes do CFM e Ministério da Saúde.
- **Segurança Jurídica para a Clínica:** Nenhum dado pessoal é exposto fora da rede interna do hospital.
- **Resiliência Relacional:** Eliminação completa de falhas HTTP 500 por estouro de tamanho de coluna em bancos PostgreSQL/MySQL.
