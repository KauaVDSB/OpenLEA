# 🏛️ ADR-005: Mecanismo de Auto-Updater Transparente (1-Click)

> **Status:** Homologada em Produção  
> **Data de Homologação:** 16/09/2026 (Refinada em 19/09/2026)  
> **Projetos de Origem:** `solicita-apac`, `sentinel`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Sistemas de automação hospitalar enfrentam mudanças constantes em layouts de portais governamentais (ex: APACnet), novas regras de periodicidade SUS e correções de segurança. Se cada atualização exigir que um técnico de TI se desloque até a máquina da faturista ou que a faturista realize procedimentos complexos de descompactação e substituição manual, o ciclo de entrega de valor é inviabilizado.

Além disso, atualizações manuais frequentemente sobrescrevem acidentalmente arquivos de configuração (`.env`) ou apagam filas de histórico local (`logs/`).

---

## 2. Decisão Arquitetural
Desenvolver um motor de **Auto-Updater 1-Click** integrado diretamente ao Sentinel Hub Gateway (`/api/v1/sentinel/handshake` e `/download/{binario}`):

```text
[ Cliente (v1.0.0) ]                                   [ Sentinel Hub Gateway ]
        │                                                        │
        │─── Handshake { app_version: "1.0.0" } ────────────────▶│
        │                                                        │
        │◀── HTTP 200 { min_required_version: "1.2.0",           │
        │               force_update: true,                      │
        │               update_url: "/download/SolicitaAPAC.exe" }
        │
[ Prompt Amigável no Terminal ]
"Deseja atualizar o SolicitaAPAC agora? [S/N]" ──▶ [ Usuário digita 'S' ]
        │
        │─── GET /download/SolicitaAPAC.exe (Streaming) ────────▶│
        │◀── Chunks com barra de progresso em tempo real ────────│
        │
[ Substituição Atômica em Disco ]
1. Baixa para arquivo temporário (.update.tmp)
2. Renomeia o executável antigo (.old)
3. Move o novo executável para o caminho canônico
4. Preserva intactos: .env, logs/ e atalhos da Área de Trabalho
```

### Regras de Implementação:
1. **Enforce de Versão no Handshake:**
   - O Sentinel compara `parse_version(app_version)` com `parse_version(min_required_version)`.
   - Se `app_version < min_required_version`, `force_update` é marcado como `True`.
2. **Download Resiliente com Barra de Progresso em Linha Única:**
   - O download utiliza streaming em chunks de 64 KB com exibição de porcentagem e barra formatada (`[====>   ] 45.2%`) em `\r` (sem floodar novas linhas no console).
3. **Substituição Atômica Multiplataforma:**
   - **No Linux:** Substitui o arquivo em `~/.local/share/...`, aplica `chmod 0o755` e restaura o atalho `.desktop`.
   - **No Windows:** Em ambiente Windows, binários em execução não podem ser sobrescritos diretamente; o updater renomeia o executável ativo para `.old` e posiciona o novo `.exe` no caminho definitivo.
4. **Preservação de Dados Locais:**
   - O updater **NUNCA** mexe no arquivo `.env` nem na subpasta `logs/`.

---

## 3. Consequências e Benefícios
- **Operação Descomplicada:** A faturista atualiza o robô com 1 tecla (`S` + Enter), sem depender de suporte técnico.
- **Rollout Imediato de Hotfixes:** Correções críticas de regras SUS chegam a 100% das máquinas em minutos.
- **Zero Corrupção de Estado:** Credenciais hospitalares e filas offline são rigorosamente preservadas.
