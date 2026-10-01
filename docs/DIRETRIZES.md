# 📜 Diretrizes de Engenharia, Qualidade e Governança - OftalmoPE Tech

> **Atenção (Desenvolvedor Humano ou Agente de IA):**  
> Antes de escrever qualquer linha de código ou realizar qualquer modificação no repositório, **LEIA ESTE DOCUMENTO NA ÍNTEGRA**, consulte o arquivo [`docs/ROADMAP.md`](./ROADMAP.md) para verificar o estado das tarefas planejadas e o catálogo em [`docs/adrs/index.md`](./adrs/index.md) para entender as restrições arquiteturais vigentes.

---

## 1. 🛡️ Segurança, Privacidade e Conformidade com a LGPD

1. **Blindagem Estrita de Dados Reais:**
   - **NUNCA** commitar arquivos contendo dados pessoais ou sensíveis de pacientes ou colaboradores (`.xlsx`, `.csv`, `.pdf`, capturas de tela com nomes ou prontuários).
   - O arquivo `.gitignore` deve conter regras ativas para bloquear planilhas, arquivos de log locais e dumps de dados temporários.
2. **Mascaramento Obrigatório de Dados (PII Masking):**
   - Dados identificáveis (CPFs, nomes, prontuários) devem ser mascarados tanto em logs de terminal quanto em relatórios:
     - CPF: `***.123.456-**` ou `111.***.***-11`.
     - Nomes de pacientes: Apenas primeiro nome e inicial ou mascaramento parcial.
3. **Telemetria de Nuvem Zero PII (ADR-003):**
   - Nenhuma informação pessoal identificável de pacientes pode ser transmitida para o Admin Hub Sentinel ou qualquer serviço cloud.
   - Apenas métricas quantitativas agregadas (total de registros, sucessos, erros tipificados, tempo de execução) são permitidas.
4. **Sanitização de Tamanho de Strings em Logs e Erros:**
   - Para garantir compatibilidade com bancos de dados relacionais em nuvem (ex: PostgreSQL/Supabase com colunas `VARCHAR(255)`), mensagens de erro e motivos de inconsistência enviados à telemetria devem ser previamente sanitizados e truncados defensivamente para **no máximo 250 caracteres** (`motivo[:247] + "..."`).
5. **Segregação de Credenciais:**
   - Senhas, chaves de API, tokens e endpoints devem residir exclusivamente no arquivo `.env`, nunca fixados diretamente no código-fonte.
   - O repositório deve fornecer um modelo canônico `.env.example` ricamente documentado.

---

## 2. 🌳 Git Flow, Conventional Commits e Revisão

1. **Padrão de Branches:**
   - `main`: Código estável, testado e homologado para produção. **NUNCA** commitar diretamente na branch `main`.
   - `feat/sprint-<numero>-<descricao-curta>`: Desenvolvimento de novas funcionalidades.
   - `fix/sprint-<numero>-<descricao-curta>`: Correções de bugs e regressões.
   - `chore/<descricao-curta>`: Ajustes de build, dependências ou infraestrutura.
2. **Conventional Commits Mandatórios:**
   Todos os commits devem seguir a convenção semântica:
   - `feat(...)`: Nova funcionalidade para o usuário ou sistema.
   - `fix(...)`: Correção de defeito ou falha de execução.
   - `docs(...)`: Alteração exclusiva de documentação ou comentários.
   - `test(...)`: Adição ou refatoração de testes unitários/integração.
   - `refactor(...)`: Mudança de código que não altera comportamento nem adiciona feature.
   - `chore(...)`: Atualização de dependências, scripts de build ou CI.
3. **Fluxo de Integração via Pull Request:**
   - Toda feature ou correção deve ser desenvolvida em branch isolada;
   - Antes de abrir PR, garanta que 100% da suíte de testes passe e atenda ao Quality Gate;
   - Realizar merge na `main` preferencialmente via **Squash and Merge**, mantendo o histórico da branch principal limpo e linear.

---

## 3. 🏗️ Arquitetura, Padrões de Código e TDD

```text
[ Apresentação / CLI / UI ]
             │
             ▼
[ Core / Orquestrador & Regras de Negócio ]  <──>  [ Dicionários & Protocolos ]
             │
             ▼
[ Services / Clientes HTTP & Scrapers ]  <──>  [ Database / Models & File Readers ]
```

1. **Arquitetura em Camadas (SOLID / SRP - ADR-001):**
   - `core/`: Configurações de ambiente, constantes, regras de negócio e orquestradores de fila. Não conhece detalhes de tela nem bibliotecas externas de banco/HTTP.
   - `database/`: Modelos de dados fortemente tipados (Pydantic / dataclasses), persistência local e leitores de arquivos (`.xlsx`, `.csv`).
   - `services/`: Clientes de API, serviços de telemetria Sentinel, parsers HTML e integrações com sistemas legados.
   - `tests/`: Suíte automatizada espelhando a estrutura do código de produção.
2. **Fail-Fast & Non-Blocking Pipeline:**
   - Se um registro individual falhar no processamento em lote, o sistema deve isolá-lo com mensagem detalhada de inconsistência e prosseguir com os demais sem travar a automação.
3. **TDD Rigoroso (Test-Driven Development):**
   - Ciclo obrigatório **Red-Green-Refactor**:
     1. Escrever o teste unitário que falha;
     2. Implementar o código mínimo necessário para o teste passar;
     3. Refatorar garantindo clareza, tipagem e performance sem quebrar os testes.
4. **BDD / Especificação em Gherkin:**
   - Cada micro-sprint deve possuir cenários de negócio descritos em linguagem ubíqua (*Funcionalidade, Cenário, Dado, Quando, Então*) antes do código.
5. **Quality Gate de Cobertura de Código:**
   - Meta mínima mandatória de **95% de cobertura de linhas e branches** monitorada via `pytest-cov`. Commits que reduzam a cobertura abaixo desse limiar devem ser corrigidos imediatamente.
6. **Testes de Mutação (Mutation Testing):**
   - Avaliação de mutantes em condições lógicas de contorno com meta mínima de **85% de mutantes eliminados (*Killed Mutants*)**, validada via `mutmut run --paths-to-mutate core,database,services`.

---

## 4. 🔄 Governança de Sprints, Milestones e Issues

1. **Milestones e Issues Prévias Obrigatórias (ADR-009):**
   - Toda sprint oficializada no planejamento **DEVE** possuir uma Milestone correspondente no GitHub.
   - Cada Micro-Sprint (`MS X.Y`) deve possuir uma Issue individual vinculada à respectiva Milestone antes do início do desenvolvimento.
2. **Sincronização Contínua em Segundo Plano:**
   - Imediatamente após a conclusão, validação de testes e commit de uma micro-sprint, a Issue correspondente no GitHub deve ser fechada (`gh issue close <id> --comment "..."`).
   - O comentário de encerramento deve reportar o commit hash, arquivos modificados e status dos testes.
3. **Regra Estrita de Encerramento de Milestone:**
   - O desenvolvedor ou agente de IA **NUNCA** encerra uma Milestone unilateralmente.
   - O encerramento da Milestone é sugerido ao operador/revisor humano **APÓS** a homologação completa e aprovação do Pull Request na branch principal (`main`).
4. **Sprints Intermediárias (Numeração Fracionária, ex: Sprint 4.5):**
   - Demandas técnicas ou operacionais críticas surgidas entre duas sprints consolidadas devem receber numeração intermediária (ex: `Sprint 4.5`), com documento específico em `docs/sprints/sprint_04_5.md` e Milestone dedicada.
5. **Política de Higienização de Armazenamento Local (Cache TTL de 5 Dias - ADR-008):**
   - Arquivos locais de telemetria e fila offline (`.sentinel_telemetry_queue.json`) operam com status `PENDING` e `SENT`.
   - Eventos com status `SENT` há mais de 5 dias corridos são expurgados automaticamente na inicialização da aplicação.
   - Eventos `PENDING` **nunca** são expurgados por TTL até que sua entrega ao Sentinel seja confirmada com HTTP 200/201.

---

## 5. 🖥️ Plataforma, Distribuição e Experiência do Usuário

1. **Distribuição Standalone Multiplataforma (ADR-006):**
   - A aplicação deve ser compilável em binário único sem depender de ambiente Python pré-instalado na máquina do usuário final (PyInstaller hermético para Windows `.exe` e Linux).
2. **Instalação Canônica Per-User sem Privilégios Administrativos (ADR-007):**
   - **Windows:** `%LOCALAPPDATA%\Programs\OftalmoPE\<NomeApp>\` + Atalho na Área de Trabalho e Menu Iniciar.
   - **Linux:** `~/.local/share/oftalmope/<nome-app>/` + Atalho XDG `.desktop` com permissão de execução e metadados de confiança (`metadata::trusted true`).
   - Não exigir elevação UAC para instalação, permitindo rollout imediato em ambientes corporativos restritos.
3. **Auto-Updater Transparente (1-Click - ADR-005):**
   - Integração nativa com o Admin Hub Sentinel (`/api/v1/sentinel/handshake` e `/download/{binario}`).
   - O app verifica atualizações ao iniciar; caso haja nova versão obrigatória ou opcional, oferece o prompt de 1 clique, realiza o download por streaming com barra de progresso em tempo real e substitui o binário atomicamente em disco sem corromper o arquivo `.env` nem o histórico de logs.
4. **Multi-Sheet Session Loop (ADR-010):**
   - Aplicações desktop baseadas em lote não devem fechar o terminal abruptamente ao fim de uma planilha. Devem oferecer loop de continuidade para processar novos arquivos na mesma sessão e aguardar tecla ENTER antes de fechar janelas disparadas por duplo-clique.
