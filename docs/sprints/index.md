# 📂 Índice de Sprints - OftalmoPE Tech

> **Visão Geral:** Este diretório contém o histórico detalhado, cenários BDD, tarefas técnicas e relatórios de entrega de cada Sprint do projeto.

---

## 🏃 Registro de Sprints

| Sprint | Nome / Foco | Status | Documento / Guia |
| :---: | :--- | :---: | :--- |
| **00** | Setup de Arquitetura, Governança e Definição de Escopo | `Em Aberto` | [INICIALIZAR_PROJETO.md](../../INICIALIZAR_PROJETO.md) |
| **01** | *[Nome da Primeira Sprint de Entrega Funcional]* | `Planejada` | *A ser criada a partir de `docs/templates/TEMPLATE_SPRINT.md`* |

---

## 🔄 Como Iniciar uma Nova Sprint
1. Crie o arquivo `docs/sprints/sprint_XX.md` copiando o modelo [`docs/templates/TEMPLATE_SPRINT.md`](../templates/TEMPLATE_SPRINT.md);
2. Atualize o [`docs/ROADMAP.md`](../ROADMAP.md) com os objetivos e micro-sprints;
3. Crie a Milestone no GitHub com o comando:
   ```bash
   gh api repos/:owner/:repo/milestones -f title="Sprint XX: Nome da Sprint" -f description="Objetivo..."
   ```
4. Crie as Issues de cada micro-sprint vinculadas à Milestone;
5. Desenvolva em branch isolada: `feat/sprint-XX-<descricao>`.
