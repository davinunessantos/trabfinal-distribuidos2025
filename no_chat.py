# ===============================================
# no_chat.py
# Módulo de Núcleo do nosso Sistema Distribuído (Nó P2P)
# ===============================================

import socket
import threading
import time
import sys
import json
# Importa as constantes que definimos no arquivo anterior
from configuracao import *

class NoChat:
    """
    Representa um único Nó (peer) na rede de chat distribuída, 
    usando threads para gerenciar as comunicações simultâneas.
    """
    def __init__(self, porta_unicast_do_no):
        # ------------------ ESTADO DO NÓ ------------------
        self.porta_unicast = porta_unicast_do_no
        self.id = None             # ID atribuído pelo Coordenador (ex: 1, 2, 3)
        self.e_coordenador = False 
        self.peers_ativos = {}     # Dicionário de peers ativos: {ID: (IP, Porta)}
        self.ativo = True          # Flag para controlar o loop infinito das threads
        
        # ------------------ SOCKETS DE REDE ------------------
        # Socket TCP (bidirecional) para comunicação Ponto a Ponto (Unicast)
        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Socket UDP (não confiável) para comunicação de Grupo (Multicast)
        self.socket_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        self.configurar_sockets()


    def configurar_sockets(self):
        """Prepara os sockets do nó (Servidor TCP e Receptor Multicast)."""
        # 1. Configurar Socket TCP (Servidor Unicast)
        try:
            self.socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Liga o socket à nossa porta individual (nosso "apartamento")
            self.socket_tcp.bind((ENDERECO_UNICAST, self.porta_unicast))
            self.socket_tcp.listen(10)
            # print(f"[STATUS] Servidor TCP escutando em: {ENDERECO_UNICAST}:{self.porta_unicast}")
        except Exception as e:
            print(f"ERRO ao configurar socket TCP: {e}")
            self.ativo = False

        # 2. Configurar Socket Multicast (Receptor UDP)
        try:
            self.socket_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Escuta na porta fixa 50000 em qualquer interface
            self.socket_multicast.bind(('', PORTA_MULTICAST))
            # Pede ao SO para se juntar ao grupo Multicast
            mreq = socket.inet_aton(IP_MULTICAST) + socket.inet_aton(ENDERECO_UNICAST)
            self.socket_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            # print(f"[STATUS] Receptor Multicast escutando em: {IP_MULTICAST}:{PORTA_MULTICAST}")
        except Exception as e:
            print(f"ERRO ao configurar socket Multicast: {e}")
            self.ativo = False


    # ====================================================================
    # THREADS E LÓGICA DE COMUNICAÇÃO (Tudo aqui roda simultaneamente)
    # ====================================================================

    def lidar_com_conexao(self, conexao, endereco):
        """
        Função executada em uma nova thread para receber dados TCP de outro nó.
        Trata a resposta JSON do Coordenador ou mensagens de chat.
        """
        try:
            dados = conexao.recv(TAMANHO_BUFFER).decode('utf-8')
            if dados:
                
                # --- NÓ COMUM RECEBENDO CADASTRO ---
                # Se o nó ainda não tem ID, a primeira conexão TCP é a resposta do Coordenador.
                if self.id is None:
                    try:
                        # Tenta converter a string recebida (JSON) em um dicionário Python
                        resposta_cadastro = json.loads(dados)
                        
                        # Atribui o ID único e a lista de peers ao estado do nó
                        self.id = resposta_cadastro['id']
                        self.peers_ativos = resposta_cadastro['peers']
                        
                        print(f"\n[CADASTRO CONCLUÍDO] Seu ID: {self.id}. Peers ativos recebidos.")
                        return # Processo de cadastro encerrado
                        
                    except json.JSONDecodeError:
                        # Se não for JSON, é uma mensagem de chat normal
                        pass 
                
                # --- RECEBIMENTO DE MENSAGEM DE CHAT ---
                print(f"\n[CHAT de {endereco[0]}:{endereco[1]}] {dados}")
                
        except Exception as e:
            pass # Ignora falhas de conexão temporárias
        finally:
            conexao.close()


    def iniciar_servidor_tcp(self):
        """[Thread: Servidor Unicast] Escuta por conexões TCP de outros nós."""
        while self.ativo:
            try:
                # Fica esperando uma conexão (bloqueante)
                conn, addr = self.socket_tcp.accept()
                # Inicia uma thread para lidar com essa conexão
                threading.Thread(target=self.lidar_com_conexao, args=(conn, addr)).start()
            except Exception:
                break

    def iniciar_receptor_multicast(self):
        """[Thread: Receptor Multicast] Escuta o canal de descoberta (Heartbeats/Entrada)."""
        while self.ativo:
            try:
                dados, endereco = self.socket_multicast.recvfrom(TAMANHO_BUFFER)
                mensagem = dados.decode('utf-8')
                
                # Se for um pedido de entrada, SÓ O COORDENADOR DEVE RESPONDER
                if mensagem == MENSAGEM_ENTRADA and self.e_coordenador:
                    self.processar_entrada_de_no(endereco)
                    
            except Exception:
                break


    def enviar_heartbeat(self):
        """[Thread: Heartbeat - APENAS COORDENADOR] Envia o sinal de vida periodicamente."""
        while self.ativo and self.e_coordenador:
            try:
                # Envia o sinal de vida para o grupo Multicast a cada 3 segundos
                self.socket_multicast.sendto(MENSAGEM_HEARTBEAT.encode('utf-8'), (IP_MULTICAST, PORTA_MULTICAST))
                time.sleep(INTERVALO_HEARTBEAT)
            except Exception:
                break


    def enviar_mensagem_chat(self, mensagem):
        """[Fan-out TCP] Envia a mensagem para todos os peers ativos (Unicast Ponto a Ponto)."""
        msg_completa = f"[ID {self.id}] {mensagem}"
        
        # Itera sobre uma cópia da lista de peers ativos
        for no_id, (ip, porta) in list(self.peers_ativos.items()):
            if no_id != self.id: # Não envia para si mesmo
                try:
                    # Tenta criar um socket temporário Cliente para enviar (Unicast)
                    s_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s_cliente.connect((ip, porta))
                    s_cliente.sendall(msg_completa.encode('utf-8'))
                    s_cliente.close()
                except Exception as e:
                    # Agora, o bloco 'try' está corretamente fechado com um 'except'
                    # Aqui ignoramos erros de conexão, assumindo que o nó falhou ou saiu (MVP)
                    pass 
