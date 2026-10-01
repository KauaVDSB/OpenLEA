# 🏛️ ADR-004: Licenciamento Centralizado, Handshake e Kill-Switch Remoto

> **Status:** Homologada em Produção  
> **Data de Homologação:** 14/09/2026  
> **Projetos de Origem:** `solicita-apac`, `sentinel`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
Os softwares da OftalmoPE Tech são ativos intelectuais e comerciais corporativos instalados diretamente em estações de trabalho de hospitais e clínicas parceiras. Se não houver controle centralizado de vigência de licença, suporte a períodos de teste (*free-trial*) e capacidade de suspensão remota (*kill-switch*), a empresa fica desprotegida contra inadimplência, uso indevido ou distribuição desautorizada.

Entretanto, uma queda momentânea de internet no hospital não pode travar uma operação crítica de faturamento se a licença estiver comprovadamente válida.

---

## 2. Decisão Arquitetural
Adotar um protocolo de comunicação seguro cliente-servidor com o **Admin Hub Sentinel**:

```text
[ SolicitaAPAC Client ]                        [ Sentinel Admin Hub (Cloud) ]
        │                                                     │
        │─── POST /api/v1/sentinel/handshake ────────────────▶│ (Valida Licença, Versão Mínima
        │    { client_id, license_key, app_version }          │  e Status do Kill-Switch)
        │                                                     │
        │◀── HTTP 200 { status: AUTHORIZED, token, grace } ───│
        │                                                     │
        │─── (Em background) POST /heartbeat a cada 15 min ──▶│ (Monitora Sessão Ativa)
```

### Regras de Operação:
1. **Handshake na Inicialização:**
   - O cliente submete `client_id`, `license_key`, `app_name`, `app_version` e `platform`.
   - Se a licença estiver ativa, o Sentinel responde com `status="AUTHORIZED"` e gera um `session_token` único criptograficamente seguro.
2. **Cache Local Criptografado/Assinado de Licença (`.sentinel_license_cache.json`):**
   - Na primeira validação online, o cliente armazena o token e a data de expiração localmente.
   - Em caso de indisponibilidade transitória da rede durante a vigência do contrato/trial, o app opera em contingência offline sem interromper o usuário.
3. **Kill-Switch Remoto com *Grace Period* de 1 Hora:**
   - Caso a diretoria acione o Kill-Switch no dashboard do Sentinel, o servidor notifica o cliente via Heartbeat ou Handshake.
   - Para não interromper o fechamento de um lote já em andamento, o app inicia uma contagem regressiva de tolerância de **1 hora** (*Grace Period*), emitindo alertas visuais até o encerramento gracioso da sessão.

---

## 3. Consequências e Benefícios
- **Governança Comercial Completa:** Controle em tempo real de quais clínicas e filiais possuem acesso ativo.
- **Resiliência Hospitalar:** Falhas de rede transitórias não paralisam a rotina médica se a licença estiver válida.
- **Encerramento Controlado:** O Kill-Switch evita perda de dados no meio de uma transação.
