# 🏛️ Histórico de Decisões Arquiteturais (ADRs) - OftalmoPE Tech

> **Catálogo Geral:** Este documento consolida as decisões arquiteturais fundamentais adotadas no ecossistema de software da OftalmoPE Tech.  
> O detalhamento extensivo de cada decisão, com diagramas de fluxo, trade-offs e regras de código, está disponível no diretório **[`docs/adrs/`](adrs/index.md)**.

---

## 📌 Arsenal de Decisões Homologadas em Produção

| ID | Título da Decisão | Status | Categoria | Documento Completo |
| :--- | :--- | :---: | :--- | :--- |
| **ADR-001** | Arquitetura em Camadas e Desacoplamento (SOLID/SRP) | **Aceita** | Core / Estrutura | [Ver Detalhes](adrs/ADR-001-arquitetura-em-camadas.md) |
| **ADR-002** | Governança de Qualidade por TDD, BDD, Cobertura 95%+ e Mutação | **Aceita** | Qualidade / Testes | [Ver Detalhes](adrs/ADR-002-qualidade-tdd-bdd-mutacao.md) |
| **ADR-003** | Conformidade LGPD Estrita, Mascaramento PII e Sanitização de Strings | **Aceita** | Segurança / LGPD | [Ver Detalhes](adrs/ADR-003-conformidade-lgpd-zero-pii.md) |
| **ADR-004** | Licenciamento Centralizado, Handshake e Kill-Switch Remoto | **Aceita** | SaaS / Sentinel | [Ver Detalhes](adrs/ADR-004-licenciamento-handshake-killswitch.md) |
| **ADR-005** | Mecanismo de Auto-Updater Transparente (1-Click) | **Aceita** | Atualização / DevOps | [Ver Detalhes](adrs/ADR-005-auto-updater-transparente.md) |
| **ADR-006** | Distribuição e Empacotamento Standalone Multiplataforma via PyInstaller | **Aceita** | Distribuição | [Ver Detalhes](adrs/ADR-006-distribuicao-multiplataforma-pyinstaller.md) |
| **ADR-007** | Instalador Corporativo Per-User sem UAC e Atalhos Automáticos | **Aceita** | Instalação / OS | [Ver Detalhes](adrs/ADR-007-instalador-corporativo-caminhos-canonicos.md) |
| **ADR-008** | Fila Local Permanente de Telemetria e Política de Expurgo TTL (5 Dias) | **Aceita** | Resiliência / SRE | [Ver Detalhes](adrs/ADR-008-fila-offline-resiliente-e-ttl.md) |
| **ADR-009** | Governança de Sprints Fracionárias e Ciclo de Vida de Issues no GitHub | **Aceita** | Governança Ágil | [Ver Detalhes](adrs/ADR-009-gestao-de-sprints-fracionarias-e-milestones.md) |
| **ADR-010** | Multi-Sheet Session Loop e Persistência de Janela no Windows | **Aceita** | Experiência Usuário | [Ver Detalhes](adrs/ADR-010-multi-sheet-session-loop.md) |
| **ADR-011** | Pre-Check de Integridade Cadastral, Caches em Memória e Triagem | **Aceita** | Auditoria Clínica | [Ver Detalhes](adrs/ADR-011-precheck-cadastral-e-caches-em-memoria.md) |
| **ADR-012** | Autoheal de Procedimentos, Médicos e Aliases com Aprendizado Local | **Aceita** | Inteligência Local | [Ver Detalhes](adrs/ADR-012-autoheal-de-procedimentos-e-aliases.md) |

---

## 📝 Como Adicionar Novas ADRs Específicas do Projeto

Quando este template for clonado para um novo projeto e surgir uma decisão de arquitetura específica do domínio (ex: escolha de driver de banco, novo protocolo de hardware, integração com leitor biométrico):

1. Crie o arquivo `docs/adrs/ADR-013-<nome-da-decisao>.md` utilizando o template em [`docs/templates/TEMPLATE_ADR.md`](templates/TEMPLATE_ADR.md);
2. Registre o novo item na tabela acima e no índice mestre [`docs/adrs/index.md`](adrs/index.md);
3. Submeta a decisão para revisão e aprovação junto ao líder técnico ou faturista responsável.
