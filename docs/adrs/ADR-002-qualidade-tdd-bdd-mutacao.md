# 🏛️ ADR-002: Governança de Qualidade por TDD, BDD, Cobertura 95%+ e Testes de Mutação

> **Status:** Homologada em Produção  
> **Data de Homologação:** 12/09/2026  
> **Projetos de Origem:** `solicita-apac`, `sentinel`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
No contexto da saúde e do faturamento hospitalar, erros de automação geram glosas financeiras irreversíveis, bloqueios no SUS/convênios e retrabalho operacional crítico. Por outro lado, testes que apenas exercitam linhas para inflar relatórios de cobertura sem validar asserções reais dão uma falsa sensação de segurança.

Precisamos de uma barreira de qualidade rigorosa (*Quality Gate*) que comprove a integridade lógica e impeça que códigos defeituosos cheguem à produção.

---

## 2. Decisão Arquitetural
Instituir uma pirâmide de qualidade mandatória composta por 4 pilares inegociáveis:

```text
       ▲
      / \     Testes de Mutação (Mutmut: >= 85% mortos)
     /   \    BDD / Gherkin (Especificação Ubíqua)
    /     \   TDD Estrito (Red-Green-Refactor)
   /───────\  Quality Gate de Cobertura (Pytest-Cov >= 95%)
```

1. **TDD Estrito (Test-Driven Development):**
   - Ciclo obrigatório:
     1. **Red:** Escrever o teste unitário reproduzindo a nova regra ou o bug relatado;
     2. **Green:** Implementar a lógica mínima estritamente necessária para aprovação do teste;
     3. **Refactor:** Limpar código, otimizar tipagem e nomenclatura mantendo todos os testes verdes.
2. **BDD / Especificação em Gherkin:**
   - Antes de codificar cada micro-sprint, os cenários de uso devem ser descritos em linguagem ubíqua:
     ```gherkin
     Funcionalidade: Pre-Check de Periodicidade SUS
       Cenário: Bloquear segundo acompanhamento com intervalo inferior a 90 dias
         Dado que o paciente possui uma APAC autorizada há 30 dias
         Quando o faturista submeter nova solicitação de Acompanhamento
         Então o sistema deve marcar o paciente como Bloqueado por Glosa
         E exibir o motivo detalhado com os dias faltantes
     ```
3. **Quality Gate de Cobertura ($\ge 95\%$):**
   - Monitoramento via `pytest-cov` cobrindo tanto linhas quanto ramificações condicionais (*branch coverage*).
   - Commits que reduzam a cobertura global abaixo de 95% são sumariamente bloqueados.
4. **Testes de Mutação (Mutation Testing com `mutmut`):**
   - Inserção sistemática de mutantes sintéticos em operadores lógicos (`>`, `<`, `==`, `!=`, `+`, `-`, inversão de booleanos) em `core/`, `database/` e `services/`.
   - **Meta Mandatória:** $\ge 85\%$ de mutantes eliminados (*Killed Mutants*). Se um teste não falhar quando a lógica de contorno for alterada, o teste é classificado como ineficaz e deve ser aprofundado.

---

## 3. Consequências e Benefícios
- **Zero Regressões em Produção:** Regras de periodicidade SUS e sanitização de payloads mantiveram 100% de precisão nos mais de 122 laudos submetidos em tempo real.
- **Documentação Viva:** Os testes BDD atuam como a especificação mais atualizada e executável do sistema.
- **Refatoração sem Medo:** A equipe e os agentes de IA podem realizar melhorias estruturais complexas com confiança total na esteira de testes.
