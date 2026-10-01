# 🏛️ ADR-010: Multi-Sheet Session Loop e Persistência de Janela no Windows

> **Status:** Homologada em Produção  
> **Data de Homologação:** 18/09/2026  
> **Projetos de Origem:** `solicita-apac`  
> **Responsável:** Equipe de Engenharia OftalmoPE Tech

---

## 1. Contexto do Problema
No fluxo de trabalho real de faturamento hospitalar, a faturista raramente processa apenas uma planilha isolada. É padrão receber arquivos separados por convênio, por médico ou por especialidade (ex: Glaucoma, Retina, Tomografias). 

Se a automação fechar a execução e o terminal imediatamente após o processamento da primeira planilha:
1. O usuário é forçado a reabrir o executável, refazer login no portal governamental e revalidar credenciais repetidas vezes;
2. Se o executável for disparado por duplo-clique no Windows (onde uma janela `cmd.exe` temporária é criada), a janela fecha instantaneamente ao término do script, impedindo o operador de ler os relatórios de erros, totais faturados e glosas prevenidas.

---

## 2. Decisão Arquitetural
Implementar no ponto de entrada (`main.py`) a máquina de estados **Multi-Sheet Session Loop**:

```text
[ Inicialização do App ] ──▶ Handshake Sentinel & Login de Sessão
                                       │
                                       ▼
┌───────────────────▶ [ Início do Loop de Planilha (Lote N) ]
│                                      │
│                                      ▼
│                             Seleção de Arquivo
│                                      │
│                                      ▼
│                         Pre-Check SUS & Injeção
│                                      │
│                                      ▼
│                         Despacho de Telemetria do Lote
│                                      │
│                                      ▼
│            "Deseja processar outra planilha nesta mesma sessão? [S/N]"
│                                      │
└── [ Digita 'S' ] ────────────────────┤
                                       │ [ Digita 'N' ou Enter ]
                                       ▼
                     "Pressione ENTER para fechar a aplicação..."
                                       │
                                       ▼
                            [ Encerramento Limpo ]
```

### Regras de Implementação:
1. **Reaproveitamento e Renovação Automática de Sessão:**
   - A sessão HTTP e os cookies de autenticação permanecem vivos entre lotes sucessivos.
   - Caso a sessão expire durante o intervalo entre planilhas, o cliente detecta o encerramento da sessão e renova o login de forma transparente antes do Lote N+1.
2. **Isolamento de Telemetria por Lote:**
   - Cada planilha processada gera seu próprio evento atômico de métricas (com identificador de lote e tempos calibrados), evitando aglutinação errônea de relatórios no Sentinel.
3. **Pausa de Saída Amigável (*Console Pause*):**
   - Ao encerrar a rotina, o script invoca `input("\nPressione ENTER para fechar a aplicação...")`, garantindo que o faturista revise os resultados com calma antes do encerramento da janela do sistema operacional.

---

## 3. Consequências e Benefícios
- **Experiência de Uso Fluida:** Elimina o atrito de múltiplos logins manuais consecutivos na rotina diária.
- **Zero Fechamentos Inesperados:** Faturistas leem os resumos e relatórios de glosas sem surpresas.
- **Economia de Recursos de Rede:** Sessões reaproveitadas reduzem a carga no servidor web legado.
