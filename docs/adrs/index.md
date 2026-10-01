# 🏛️ Arsenal de Decisões Arquiteturais (ADRs Homologadas) - OftalmoPE Tech

> **Visão Geral:** Este diretório contém o **Arsenal Técnico e Arquitetural Homologado** da OftalmoPE Tech.  
> Cada ADR documenta uma decisão testada e comprovada em produção hospitalar real, detalhando o contexto, problema, solução arquitetada, trade-offs e diretrizes de implementação para novos projetos.

---

## 🧭 Índice do Arsenal por Categoria

### 🏗️ 1. Arquitetura, Qualidade & Dados
* **[ADR-001: Arquitetura em Camadas e Desacoplamento SOLID/SRP](ADR-001-arquitetura-em-camadas.md):** Estrutura canônica (`core/`, `database/`, `services/`, `tests/`) que permite evolução de CLI para UI e de SQLite para nuvem sem acoplamento.
* **[ADR-002: Governança de Qualidade por TDD, BDD, Cobertura 95%+ e Mutação](ADR-002-qualidade-tdd-bdd-mutacao.md):** Ciclo Red-Green-Refactor, especificações em Gherkin, Quality Gate de 95% de linhas e branches, e esteira `mutmut` (meta $\ge 85\%$ de mutantes eliminados).
* **[ADR-003: Conformidade LGPD Estrita, Mascaramento PII e Sanitização de Strings](ADR-003-conformidade-lgpd-zero-pii.md):** Mascaramento de dados sensíveis em logs/telas, telemetria Zero PII para nuvem e truncamento defensivo ($\le 250$ caracteres) para evitar estouro em bancos relacionais.

### 🛡️ 2. Licenciamento SaaS, Telemetria & Resiliência
* **[ADR-004: Licenciamento Centralizado, Handshake e Kill-Switch Remoto](ADR-004-licenciamento-handshake-killswitch.md):** Integração com o Admin Hub Sentinel, validação de chaves de licença, períodos de free-trial e encerramento remoto gracioso com *grace period* de 1 hora.
* **[ADR-005: Mecanismo de Auto-Updater Transparente (1-Click)](ADR-005-auto-updater-transparente.md):** Enforce de versão mínima pelo Sentinel, download de binário por streaming com barra de progresso em tempo real e substituição atômica sem corromper `.env` nem logs.
* **[ADR-008: Fila Local Permanente de Telemetria e Política de Expurgo TTL (5 Dias)](ADR-008-fila-offline-resiliente-e-ttl.md):** Persistência offline em `.sentinel_telemetry_queue.json` com status `PENDING`/`SENT`, tentativa de reenvio automático (*auto-flush*) na inicialização e expurgo seguro após 5 dias apenas de eventos entregues.

### 💻 3. Distribuição, Instalação & Experiência Multiplataforma
* **[ADR-006: Distribuição e Empacotamento Standalone Multiplataforma via PyInstaller](ADR-006-distribuicao-multiplataforma-pyinstaller.md):** Script canônico `build_exe.py` que gera executável hermético para Windows (`.exe`) e Linux, sem necessidade de Python ou dependências instaladas na ponta.
* **[ADR-007: Instalador Corporativo Per-User sem UAC e Atalhos Automáticos](ADR-007-instalador-corporativo-caminhos-canonicos.md):** Caminhos padronizados corporativos (`%LOCALAPPDATA%\Programs\OftalmoPE\<App>` no Windows e `~/.local/share/oftalmope/<app>` no Linux) com criação de atalhos confiáveis na Área de Trabalho e Menu Iniciar.
* **[ADR-010: Multi-Sheet Session Loop e Persistência de Janela](ADR-010-multi-sheet-session-loop.md):** Ponto de entrada interativo seguro (Dry-Run por padrão, Live com confirmação), processamento contínuo de múltiplos lotes sem reiniciar e pausa antes do encerramento para evitar fechamento de tela após duplo-clique.

### 🔬 4. Inteligência Clínica, Auditoria & Governança
* **[ADR-009: Governança de Sprints Fracionárias e Ciclo de Vida de Issues no GitHub](ADR-009-gestao-de-sprints-fracionarias-e-milestones.md):** Regras de Milestones prévias, encerramento em segundo plano após cada commit e padronização de sprints intermediárias (ex: Sprint 4.5).
* **[ADR-011: Pre-Check Cadastral, Caches em Memória e Telemetria de Triagem](ADR-011-precheck-cadastral-e-caches-em-memoria.md):** Separação mandatória entre etapa de auditoria prévia e etapa de injeção real, eliminando requisições redundantes com caches $O(1)$ e registrando horas poupadas mesmo em lotes sem laudos aprovados.
* **[ADR-012: Autoheal de Procedimentos, Médicos e Aliases com Aprendizado Local](ADR-012-autoheal-de-procedimentos-e-aliases.md):** Dynamic Aliasing para variações de grafia em planilhas hospitalares, com seletor interativo na primeira ocorrência, gravação em cache persistente local (`aliases_cache.json`) e sincronização central via Sentinel.

---

## 📊 Matriz de Aplicação em Novos Projetos

| Se o novo projeto for... | ADRs Mandatórias | ADRs Opcionais / Futuras |
| :--- | :--- | :--- |
| **Robô Desktop / Automação RPA** | ADR-001, 002, 003, 004, 005, 006, 007, 008, 010, 011 | ADR-012 (Autoheal) |
| **Microserviço / API de Integração** | ADR-001, 002, 003, 004, 008, 009 | ADR-005, 006, 007 (Deploy via Container) |
| **Interface Gráfica (PySide6 / Web)** | ADR-001, 002, 003, 004, 005, 007, 010, 011, 012 | ADR-006 |
| **Processador de Planilhas / ETL** | ADR-001, 002, 003, 008, 010, 011, 012 | ADR-005, 006 |
