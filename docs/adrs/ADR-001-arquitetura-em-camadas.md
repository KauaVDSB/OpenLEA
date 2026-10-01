# 🏛️ ADR-001: Arquitetura em Camadas e Desacoplamento SOLID/SRP

> **Status:** Homologada em Produção  
> **Data de Homologação:** 10/09/2026  
> **Projetos de Origem:** `solicita-apac`, `sentinel`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Os softwares da OftalmoPE Tech nascem tipicamente para resolver gargalos operacionais urgentes no ambiente hospitalar (ex: automação de laudos, faturamento, conciliação de agendas, triagem). Se forem implementados como scripts monolíticos, tornam-se frágeis, difíceis de testar e impossíveis de migrar para interfaces gráficas (PySide6), filas assíncronas ou bancos de dados relacionais.

Precisamos de uma arquitetura limpa e padrão que garanta desacoplamento total entre regras de negócio, persistência, integrações externas e interface com o usuário.

---

## 2. Decisão Arquitetural
Adotar a **Clean Architecture** simplificada com separação estrita em 4 camadas orientadas ao Princípio da Responsabilidade Única (SRP):

```text
┌────────────────────────────────────────────────────────┐
│               Apresentação / CLI / UI                  │  (main.py / views)
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│          core/ (Regras de Negócio & Orquestração)      │  (dispatcher, config, regras)
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
┌─────────────▼──────────────┐  ┌──────────▼─────────────┐
│  services/ (APIs, Scrapers)│  │ database/ (Models, ETL)│
└────────────────────────────┘  └────────────────────────┘
```

1. **`core/` (Núcleo de Negócio):**
   - Contém as regras clínicas/financeiras, dicionários de códigos (ex: tabela SUS/TUSS), validações e orquestradores de fluxo.
   - **Regra:** Não pode importar de `main.py`, nem de bibliotecas específicas de renderização visual ou frameworks web.
2. **`database/` (Persistência & Modelos):**
   - Contém modelos de dados tipados (Pydantic / dataclasses), leitores de arquivos (`openpyxl`, `pandas`), DAOs e sessões ORM (SQLAlchemy).
   - **Regra:** Não toma decisões clínicas nem regras de periodicidade; apenas ingere, serializa e persiste.
3. **`services/` (Integrações Externas):**
   - Contém clientes HTTP (`httpx`), clientes de telemetria e licença (`telemetry_service.py`, `license_client.py`), parsers de HTML (`BeautifulSoup4`).
   - **Regra:** Não interage diretamente com o usuário nem exibe mensagens no terminal.
4. **`tests/` (Suíte de Testes Automatizados):**
   - Espelha estritamente a árvore de código (`tests/test_core_*.py`, `tests/test_services_*.py`, etc.) utilizando mocks e dados sintéticos.

---

## 3. Consequências e Benefícios
- **Substituição Transparente de Interface:** Uma rotina iniciada em CLI pode ser consumida por uma interface PySide6/QML ou API FastAPI sem modificar uma linha do `core/` ou dos `services/`.
- **Testabilidade 100% Determinística:** Todas as integrações de rede e leituras de arquivos podem ser mockadas com facilidade no pytest.
- **Onboarding Acelerado:** Qualquer engenheiro ou agente de IA que entra em um projeto da OftalmoPE Tech já conhece previamente onde cada responsabilidade reside.
