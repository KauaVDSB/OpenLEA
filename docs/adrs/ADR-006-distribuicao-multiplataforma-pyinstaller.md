# 🏛️ ADR-006: Distribuição e Empacotamento Standalone Multiplataforma via PyInstaller

> **Status:** Homologada em Produção  
> **Data de Homologação:** 15/09/2026  
> **Projetos de Origem:** `solicita-apac`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Estações de trabalho hospitalares possuem fortes restrições de segurança:
- Faturistas e recepcionistas não têm permissão para instalar interpretadores Python, pip, compiladores C ou variáveis de ambiente de sistema.
- Versões de SO variam entre Windows 10/11 x64 nas clínicas e Linux (Ubuntu/Debian) nos servidores de backend e estações de desenvolvimento da TI.
- O software precisa rodar "out-of-the-box" com duplo-clique, sem falhas de bibliotecas dinâmicas ausentes (`DLLs` / `.so`).

---

## 2. Decisão Arquitetural
Adotar o **PyInstaller** orquestrado por um script canônico de automação de build ([`build_exe.py`](../../build_exe.py)):

```text
Código-Fonte Python (.py)
         │
         ▼
[ build_exe.py ]
  ├── Coleta de dependências e hidden imports (httpx, beautifulsoup4, openpyxl)
  ├── Inclusão de recursos estáticos e metadados PE (Windows FileVersion / CompanyName)
  ├── Configuração de manifesto 'asInvoker' (sem requisição de UAC)
  └── Compilação com flag --onefile e --console
         │
         ▼
[ Binário Standalone Hermético ]
  ├── Windows: dist/SolicitaAPAC.exe (~38 MB)
  └── Linux:   dist/solicita-apac   (~47 MB)
```

### Regras do Pipeline de Compilação:
1. **Script Único de Build Multiplataforma (`build_exe.py`):**
   - Detecta o sistema operacional hospedeiro (`platform.system()`);
   - No Windows, compila `NomeApp.exe` incluindo ícone corporativo (`.ico`) e metadados de versão PE;
   - No Linux, compila o executável ELF standalone `nome-app` e ajusta permissões `0o755`.
2. **Resolução Dinâmica do Diretório Base (`BASE_DIR`):**
   - Quando compilado via PyInstaller, arquivos locais residem no diretório do executável (`sys.executable`), enquanto no modo script residem na raiz do projeto:
     ```python
     if getattr(sys, "frozen", False):
         BASE_DIR = Path(sys.executable).resolve().parent
     else:
         BASE_DIR = Path(__file__).resolve().parent.parent
     ```
   - Essa técnica garante que o executável standalone localize o `.env` e a pasta `logs/` sem criar caminhos fantasmas na pasta temporária `_MEIxxxxxx`.
3. **CI Multi-Branch no GitHub Actions:**
   - Pipeline `.github/workflows/ci.yml` que testa o código no Ubuntu e no Windows runner em paralelo, gerando artefatos de release automaticamente em cada tag `v*.*.*`.

---

## 3. Consequências e Benefícios
- **Instalação Zero-Dependency:** O usuário final precisa apenas do arquivo executável único.
- **Portabilidade Total:** Funciona de forma idêntica no Windows do faturamento e no Ubuntu do laboratório de TI.
- **Isolamento de Ambiente:** Elimina conflitos de versões de Python ou pacotes conflitantes no sistema hospedeiro.
