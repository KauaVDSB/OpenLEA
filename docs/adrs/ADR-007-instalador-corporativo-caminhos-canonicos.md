# 🏛️ ADR-007: Instalador Corporativo Per-User sem UAC e Atalhos Automáticos

> **Status:** Homologada em Produção  
> **Data de Homologação:** 16/09/2026 (Refinada em 19/09/2026)  
> **Projetos de Origem:** `solicita-apac`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Tradicionalmente, instaladores de software corporativo no Windows gravam em `C:\Program Files\`, exigindo privilégios de Administrador (elevação UAC). Nas clínicas do Hospital de Olhos, os computadores dos operadores são bloqueados pela equipe de TI; cada solicitação de UAC exige agendamento de chamado técnico e trava a implantação.

Além disso, deixar executáveis soltos na pasta `Downloads` ou diretamente na Área de Trabalho provoca desorganização, exclusões acidentais de arquivos de configuração e perda de histórico de telemetria.

---

## 2. Decisão Arquitetural
Adotar a estratégia **Per-User Corporate Installation** orquestrada pelo script canônico ([`installer.py`](../../installer.py)):

```text
Usuário executa instalador ou 'SolicitaAPAC.exe --install'
                           │
      ┌────────────────────┴────────────────────┐
      ▼                                         ▼
[ Ambiente Windows ]                      [ Ambiente Linux ]
%LOCALAPPDATA%\Programs\OftalmoPE\<App>\  ~/.local/share/oftalmope/<app>/
├── <App>.exe                             ├── <App>
├── .env (credenciais protegidas)         ├── .env
└── logs/ (filas offline e auditoria)     └── logs/
      │                                         │
      ▼                                         ▼
Criação Automática de Atalhos:            Criação de Atalhos XDG:
• Desktop: %USERPROFILE%\Desktop\<App>.lnk • Desktop: ~/Desktop/<App>.desktop (trusted)
• Menu Iniciar: Start Menu\Programs\...   • Menu: ~/.local/share/applications/...
```

### Regras de Implementação:
1. **Sem Elevação UAC:**
   - A pasta `%LOCALAPPDATA%` (Windows) e `~/.local/share/` (Linux) pertence exclusivamente ao usuário logado, permitindo instalação, execução e auto-atualização sem permissão de root ou administrador.
2. **Criação de Atalhos Oficiais com Ícone e Diretório de Trabalho:**
   - **No Windows:** Cria atalho `.lnk` via VBScript / WScript.Shell com `WorkingDirectory` apontando para o diretório canônico da aplicação (evitando que o app procure o `.env` no Desktop).
   - **No Linux:** Cria lançador `.desktop` padrão XDG, define permissão `0o755` e registra metadados de confiança no GNOME/XFCE (`gio set <atalho> metadata::trusted true`), eliminando o diálogo de aviso *"Untrusted application launcher"*.
3. **Migração Idempotente de Instalações Legadas:**
   - O instalador verifica automaticamente se existem pastas antigas provisórias (ex: `Documents\K\`) e move o `.env` e as filas de telemetria existentes para o novo local oficial sem perda de dados.
4. **Isolamento em Testes Unitários:**
   - As rotinas de teste (`test_installer.py`) devem conter mocks para a criação de atalhos, garantindo que a execução do `pytest` jamais altere os atalhos reais da Área de Trabalho do desenvolvedor.

---

## 3. Consequências e Benefícios
- **Instalação Instantânea:** Faturistas instalam a aplicação sem depender de chamados para o suporte de TI.
- **Área de Trabalho Limpa:** Fica apenas o atalho oficial de lançamento; executáveis e configurações ficam organizados no diretório corporativo padrão.
- **Ambiente Blindado para o Auto-Updater:** O updater substitui o binário dentro da pasta oficial sem risco de quebrar links ou permissões.
