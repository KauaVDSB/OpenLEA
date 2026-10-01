# 🏛️ ADR-009: Governança de Sprints Fracionárias e Ciclo de Vida de Issues no GitHub

> **Status:** Homologada em Produção  
> **Data de Homologação:** 13/09/2026 (Atualizada em 17/09/2026)  
> **Projetos de Origem:** `solicita-apac`, `sentinel`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
O desenvolvimento em ritmos acelerados (com agentes de IA e múltiplos desenvolvedores) pode facilmente gerar desalinhamento: issues esquecidas abertas, código entregue sem rastreabilidade de requisitos, e marcos (*Milestones*) finalizados sem aprovação formal do líder técnico.

Além disso, em operações hospitalares reais frequentemente surgem demandas técnicas críticas urgentes entre duas sprints de roadmap previamente consolidadas (ex: uma necessidade de telemetria cloud imediata antes de iniciar a interface gráfica). Forçar essas tarefas para a sprint seguinte atrasa o escopo planejado, enquanto inseri-las retroativamente corrompe o histórico da sprint anterior.

---

## 2. Decisão Arquitetural
Instituir a **Governança Estrita de Milestones, Issues Contínuas e Sprints Fracionárias**:

```text
Planejamento da Sprint ──▶ Criação Prévia de Milestone no GitHub
                                    │
                                    ▼
       Criação de Issues Individuais para cada Micro-Sprint (MS X.Y)
                                    │
                                    ▼
[ Desenvolvimento ] ──▶ [ Testes Verdes ] ──▶ [ Commit Semântico ]
                                                      │
                                                      ▼
                       Fechamento Contínuo em Segundo Plano:
                       gh issue close <id> --comment "Commit <hash>, 100% testes"
                                                      │
                                                      ▼
                       Pull Request na branch principal 'main'
                                                      │
                                                      ▼
                 Aprovação Humana ──▶ Sugestão Formal de Encerramento da Milestone
```

### Regras de Operação:
1. **Milestones e Issues Prévias Obrigatórias:**
   - Nenhum código de feature ou refatoração deve ser iniciado sem que a Milestone correspondente e suas Issues estejam abertas no repositório GitHub.
2. **Fechamento Contínuo em Background:**
   - Imediatamente após a conclusão, validação de testes e commit de uma micro-sprint, o desenvolvedor ou agente de IA **DEVE** fechar a Issue vinculada via CLI (`gh issue close <id> --comment "..."`).
   - O comentário deve documentar de forma reprodutível: hash do commit, arquivos modificados e sumário da suíte de testes.
3. **Regra de Encerramento de Milestone:**
   - O agente ou desenvolvedor **NUNCA** fecha uma Milestone de forma unilateral.
   - O fechamento da Milestone é sugerido ao operador/revisor humano **APÓS** a aprovação final do PR e merge na branch `main`.
4. **Sprints Intermediárias / Fracionárias (ex: Sprint 4.5):**
   - Demandas técnicas ou operacionais críticas surgidas entre duas sprints planejadas que precisam ser concluídas antes da próxima etapa do roadmap recebem numeração com fração (ex: `Sprint 4.5`).
   - Requisitos:
     1. Documento dedicado em `docs/sprints/sprint_XX_5.md`;
     2. Milestone própria no GitHub cadastrada antes da codificação;
     3. Branch dedicada: `feat/sprint-XX.5-<descricao>`.

---

## 3. Consequências e Benefícios
- **Rastreabilidade Absoluta:** Qualquer stakeholder sabe exatamente qual commit entregou qual requisito.
- **Flexibilidade com Disciplina:** Sprints fracionárias permitem adaptação a emergências hospitalares sem bagunçar a linha do tempo do roadmap.
- **Clareza de Entrega:** O estado das Issues reflete fielmente o progresso em tempo real da equipe.
