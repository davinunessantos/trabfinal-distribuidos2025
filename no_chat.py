# ===============================================
# no_chat.py
# Módulo de Núcleo do nosso Sistema Distribuído (Nó P2P)
# ===============================================

import socket
import threading
import time
import sys
import json
from configuracao import *

class NoChat:
    """
    Representa um único Nó (peer) na rede de chat distribuída.
    Gerencia o estado (ID, peers_ativos) e as threads de comunicação.
    """
    def __init__(self, porta_unicast_do_no):
        # ------------------ ESTADO DO NÓ ------------------
        self.porta_unicast = porta_unicast_do_no
        self.id = None             
        self.e_coordenador = False 
        self.peers_ativos = {}     
        self.ativo = True          
        
        # ------------------ SOCKETS DE REDE ------------------
        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_multicast = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        self.configurar_sockets()


    def configurar_sockets(self):
        """Prepara os sockets do nó (Servidor TCP e Receptor Multicast)."""
        # 1. Configurar Socket TCP (Servidor Unicast)
        try:
            self.socket_tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_tcp.bind((ENDERECO_UNICAST, self.porta_unicast))
            self.socket_tcp.listen(10)
            print(f"[STATUS] Servidor TCP escutando em: {ENDERECO_UNICAST}:{self.porta_unicast}")
        except Exception as e:
            print(f"ERRO ao configurar socket TCP: {e}")
            self.ativo = False

        # 2. Configurar Socket Multicast (Receptor UDP)
        try:
            self.socket_multicast.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_multicast.bind(('', PORTA_MULTICAST))
            
            # Necessário usar o IP numérico (IP_LOCALHOST) para o SO se juntar ao grupo
            mreq = socket.inet_aton(IP_MULTICAST) + socket.inet_aton(IP_LOCALHOST)
            self.socket_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            print(f"[STATUS] Receptor Multicast escutando em: {IP_MULTICAST}:{PORTA_MULTICAST}")
        except Exception as e:
            print(f"ERRO ao configurar socket Multicast: {e}")
            self.ativo = False


    # ====================================================================
    # THREADS E LÓGICA DE COMUNICAÇÃO
    # ====================================================================

    def lidar_com_conexao(self, conexao, endereco):
        """Trata o recebimento de dados TCP (Cadastro, Atualização de Roster ou Chat)."""
        try:
            dados = conexao.recv(TAMANHO_BUFFER).decode('utf-8')
            if not dados:
                return

            # --- 1. Tenta tratar como JSON (Controle: Cadastro ou Atualização) ---
            try:
                data_json = json.loads(dados)
                
                # LÓGICA DE CADASTRO INICIAL (Se ainda não tem ID)
                if self.id is None and 'id' in data_json:
                    self.id = data_json['id']
                    self.peers_ativos = data_json['peers']
                    print(f"\n[CADASTRO CONCLUÍDO] Seu ID: {self.id}. Peers ativos recebidos.")
                    return 
                
                # LÓGICA DE ATUALIZAÇÃO DE ROSTER (Para nós já existentes)
                elif data_json.get('tipo') == 'ROSTER_UPDATE':
                    self.peers_ativos = data_json['peers']
                    print(f"\n[ROSTER UPDATE] Roster de peers atualizado pelo Coordenador.")
                    return 

            except json.JSONDecodeError:
                # Se não for JSON, é uma mensagem de CHAT.
                pass
            
            # --- 2. Trata como Mensagem de CHAT ---
            print(f"\n[CHAT de {endereco[0]}:{endereco[1]}] {dados}")
                
        except Exception as e:
            pass 
        finally:
            conexao.close()


    def iniciar_servidor_tcp(self):
        """[Thread: Servidor Unicast] Escuta por conexões TCP de outros nós."""
        while self.ativo:
            try:
                conn, addr = self.socket_tcp.accept()
                threading.Thread(target=self.lidar_com_conexao, args=(conn, addr)).start()
            except Exception:
                break

    def iniciar_receptor_multicast(self):
        """[Thread: Receptor Multicast] Escuta o canal de descoberta (Heartbeats/Entrada)."""
        while self.ativo:
            try:
                dados, endereco = self.socket_multicast.recvfrom(TAMANHO_BUFFER)
                mensagem_raw = dados.decode('utf-8')
                
                try:
                    mensagem = json.loads(mensagem_raw)
                    
                    if mensagem.get('tipo') == MENSAGEM_ENTRADA and self.e_coordenador:
                        self.processar_entrada_de_no(mensagem)
                        
                except json.JSONDecodeError:
                    if mensagem_raw == MENSAGEM_HEARTBEAT:
                         pass
                    
            except Exception:
                break


    def enviar_heartbeat(self):
        """[Thread: Heartbeat - APENAS COORDENADOR] Envia o sinal de vida periodicamente."""
        while self.ativo and self.e_coordenador:
            try:
                self.socket_multicast.sendto(MENSAGEM_HEARTBEAT.encode('utf-8'), (IP_MULTICAST, PORTA_MULTICAST))
                time.sleep(INTERVALO_HEARTBEAT)
            except Exception:
                break


    def enviar_mensagem_chat(self, mensagem):
        """[Fan-out TCP] Envia a mensagem para todos os peers ativos (Unicast Ponto a Ponto)."""
        msg_completa = f"[ID {self.id}] {mensagem}"
        
        # O nó agora tem a lista COMPLETA para fazer o Fan-out
        for no_id, (ip, porta) in list
