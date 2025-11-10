# ===============================================
#configuracao.py
# Módulo de Configuração do nosso Chat
# Usado por todos os nós para saberem onde e como se comunicar.
# ===============================================

# 1. Endereçamento UNICAST (Comunicação Ponto a Ponto e Chat)
# -------------------------------------------------------------
# Endereço legível que usamos para o socket.bind
ENDERECO_UNICAST = 'localhost' 

#Endereço numérico (127.0.0.1), obrigatório para configurações internas do socket.
IP_LOCALHOST = '127.0.0.1' 

# Porta inicial a ser usada. O primeiro nó usará esta porta, 
# o segundo usará (PORTA_BASE_UNICAST + 1), e assim por diante.
PORTA_BASE_UNICAST = 50010 


# 2. Endereçamento MULTICAST (Descoberta e Heartbeat de Grupo)
# -------------------------------------------------------------
# Endereço reservado da Classe D (224.x.x.x) para comunicação de grupo.
IP_MULTICAST = '224.1.1.1' 

# Porta fixa para o canal de Multicast. Todos os nós escutam nesta porta.
PORTA_MULTICAST = 50000 


# 3. Parâmetros de Tempo e Controle
# ----------------------------------
# O Coordenador enviará seu sinal de vida (heartbeat) a cada 3 segundos.
INTERVALO_HEARTBEAT = 3 

# Tamanho máximo do buffer de recepção (em bytes).
TAMANHO_BUFFER = 1024 


# 4. Mensagens de Controle (Protocolo Interno)
# ----------------------------------
MENSAGEM_ENTRADA = "QUERO_ENTRAR"
MENSAGEM_HEARTBEAT = "VIVO"
