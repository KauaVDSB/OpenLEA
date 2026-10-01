# 🏛️ ADR-012: Autoheal de Procedimentos, Médicos e Aliases com Aprendizado Local

> **Status:** Homologada em Arquitetura (Em Implantação)  
> **Data de Homologação:** 19/09/2026  
> **Projetos de Origem:** `solicita-apac`, `SolicitaMV`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Planilhas hospitalares extraídas de sistemas de gestão (como SMART, MV ou Tasy) apresentam frequentemente variações de digitação, abreviações e inconsistências de nomenclatura inseridas por diferentes recepcionistas e faturistas:
- Variações médicas: `DRA. MARIA SILVA`, `MARIA SILVA`, `DRA MARIA SILVA - CRM 1234`, `M. SILVA`;
- Variações de procedimentos: `ACOMP GLAUCOMA`, `CONS ACOMP GLAUCOMA`, `GLAUCOMA ACOMPANHAMENTO`, `030101011-0`.

Se o software depender exclusivamente de um dicionário estático rígido (`dicionario.py`), cada nova variação de escrita causará a rejeição do registro como inconsistência, exigindo alterações manuais no código-fonte ou edições manuais na planilha pela faturista.

---

## 2. Decisão Arquitetural
Implementar um mecanismo inteligente de **Autoheal e Resolução Dinâmica de Aliases (Dynamic Aliasing)** com cache de aprendizado local persistente:

```text
[ Termo da Planilha: "DRA MARIA SILVA" ]
                   │
                   ▼
     Existe no Dicionário Estático?
     ├── SIM ──▶ Mapeia diretamente em O(1)
     └── NÃO
          │
          ▼
     Existe no Cache de Aprendizado Local (aliases_cache.json)?
     ├── SIM ──▶ Resolve automaticamente com o alias memorizado
     └── NÃO
          │
          ▼
   Prompt Interativo de Resolução (CLI ou Modal UI):
   "O termo 'DRA MARIA SILVA' não foi reconhecido.
    Deseja associar ao médico homologado:
    [1] JOAO OCTAVIO PIRES (CRM 101386)
    [2] MARIA SILVA DE SOUZA (CRM 109921)
    [O] Outro CRM..."
          │
          ▼ [ Usuário seleciona [2] uma única vez ]
   1. Aplica a correção imediatamente no lote atual;
   2. Grava permanentemente em aliases_cache.json;
   3. (Opcional) Sincroniza com o Sentinel Hub para compartilhar
      o aprendizado com todas as estações da clínica.
```

### Regras de Operação:
1. **Prioridade de Resolução:**
   - 1º: Dicionário oficial canônico do projeto;
   - 2º: Cache local de autoheal homologado (`LOGS_DIR / "aliases_cache.json"`);
   - 3º: Intervenção assistida do operador na primeira ocorrência.
2. **Persistência Segura:**
   - O arquivo de cache deve ser formatado em JSON legível com campos: termo de entrada, código mapeado, data da resolução e operador responsável.
3. **Sincronização Centralizada com o Sentinel:**
   - Termos homologados em uma estação de trabalho podem ser exportados via API REST para o Sentinel e distribuídos para os demais robôs da mesma clínica no próximo Handshake.

---

## 3. Consequências e Benefícios
- **Autonomia Crescente:** Quanto mais o sistema opera na clínica, mais inteligente e resiliente ele se torna.
- **Redução de Intervenções:** Elimina retrabalho de suporte para variações triviais de grafia.
- **Padronização Hospitalar:** Alinha o cadastro de médicos e procedimentos entre os diferentes turnos da clínica.
