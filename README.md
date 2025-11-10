## 📝 README.md

# Sistema de Chat Distribuído P2P (MVP)
-Por Davi Nunes, C.COMP UERJ

**LINK PARA OS ARQUIVOS NO GIT:**
https://github.com/davinunessantos/trabfinal-distribuidos2025

## 🎯 Propósito do Projeto

Este é o trabalho final da Disicplina de Sistemas Distribuídos
Consiste no desenvolvimento de um **Sistema de Mensagens Instantâneas Distribuído** seguindo a arquitetura **Peer-to-Peer (P2P)**. O objetivo principal é demonstrar o estabelecimento de uma rede sem servidor central, focando na **entrada de novos nós via Multicast** e na **comunicação de grupo** (Fan-out).

-----

## 🚧 Sacrifícios e Escopo Reduzido (MVP)

Devido às limitações de tempo e para garantir a entrega de uma solução funcional dentro do prazo, alguns requisitos mais complexos foram **intencionalmente sacrificados**, mantendo-se a essência distribuída do sistema:

1.  **Tolerância a Falhas:** O sistema **não implementa a Eleição Automática** de um novo Coordenador. Se o nó Coordenador falhar, a rede será paralisada, pois novos nós não poderão entrar.
2.  **Consistência Perfeita:** Não há mecanismos avançados (como vetores de tempo) para garantir uma ordem causal perfeita das mensagens. A consistência se limita ao princípio de **Fan-out (Broadcast)**, onde cada nó distribui a mensagem para todos os peers que ele conhece.

**Essência Mantida:**

  * Arquitetura **P2P** (todo nó é Cliente e Servidor).
  * Mecanismo de **Descoberta de Coordenador via Multicast**.
  * Comunicação **Heartbeat** pelo Coordenador (sinalização de vida).
  * Cadastro e Distribuição do **Roster de Peers** pelo Coordenador.

-----

## ⚙️ Arquivos do Projeto

  * **`configuracao.py`**: Define as constantes de rede (IPs Multicast, Portas Base, Tempo de Heartbeat).
  * **`no_chat.py`**: Contém a classe principal (`NoChat`), implementando toda a lógica P2P, as *threads* de escuta (TCP e Multicast) e o protocolo de entrada.

-----

## 🚀 Instruções de Execução (Ambiente WSL/Linux)

Para simular a rede, inicie a aplicação em **diferentes terminais do WSL**, usando portas Unicast únicas para cada instância.

1.  **Acesse o Diretório:**

    ```bash
    cd ~/[diretorio]/trabfinal-distribuidos2025
    ```

2.  **Iniciar o Coordenador (ID 1):**
    O Coordenador **deve ser o primeiro a ser iniciado** e deve usar a **Porta Base** (`50010`). Ele assume o papel de gerenciar o cadastro.

    ```bash
    python3 no_chat.py 50010
    ```

3.  **Iniciar os Nós Comuns (Ex: ID 2, ID 3, ID 4...):**
    Abra novos terminais para cada nó. As portas devem ser **diferentes** da Porta Base, mas **não precisam ser imediatamente sequenciais** (ex: 50011, 50020, 50030 funcionam).

    ```bash
    # Exemplo para o Nó 2:
    python3 no_chat.py 50011 

    # Exemplo para o Nó 3:
    python3 no_chat.py 50012 
    ```

### Observações Importantes:

  * **Comunicação de Grupo:** A comunicação de *chat* só funcionará após o Nó Comum receber a mensagem **`[CADASTRO CONCLUÍDO]`**.
  * **Roster Completo:** O Coordenador envia o Roster atualizado (via `ROSTER_UPDATE`) para todos os nós existentes **toda vez** que um novo nó entra, garantindo que o chat funcione para todos os pares.
  * **Heartbeat:** O Coordenador envia um *heartbeat* a cada 3 segundos via Multicast, mas a rede não reage à sua falha.
