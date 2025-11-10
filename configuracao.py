# ===============================================
#configuracao.py
# Módulo de Configuração do nosso Chat
# Usado por todos os nós para saberem onde e como se comunicar.
# ===============================================

# 1. Endereçamento UNICAST (Comunicação Ponto a Ponto e Chat)
# -------------------------------------------------------------
# 'localhost' ou '127.0.0.1' - Endereço de loopback para simular
# múltiplos nós na mesma máquina (WSL).
ENDERECO_UNICAST = 'localhost' 

# Porta inicial para os Nós. O primeiro nó usará 50010, o segundo 50011, etc.
# Isso permite que cada nó escute em um 'apartamento' diferente.
PORTA_BASE_UNICAST = 50010 


# 2. Endereçamento MULTICAST (Descoberta e Heartbeat de Grupo)
# -------------------------------------------------------------
# Endereço reservado da Classe D (224.x.x.x). 
# Usado para 'anunciar' a entrada na rede e enviar o sinal de vida do Coordenador.
IP_MULTICAST = '224.1.1.1' 

# Porta fixa para o canal de Multicast. Todos os nós escutam aqui.
PORTA_MULTICAST = 50000 


# 3. Parâmetros de Tempo e Controle
# ----------------------------------
# O Coordenador enviará seu sinal de vida (heartbeat) a cada 3 segundos.
# A ausência desse sinal seria usada para detectar falha (sacrificado aqui).
INTERVALO_HEARTBEAT = 3 

# Tamanho máximo do buffer de recepção (em bytes).
TAMANHO_BUFFER = 1024 


# 4. Mensagens de Controle (Protocolo Interno)
# ----------------------------------
# Strings usadas para padronizar o que os nós enviam para o canal Multicast.
MENSAGEM_ENTRADA = "QUERO_ENTRAR"
MENSAGEM_HEARTBEAT = "VIVO"
