# ===============================================
# no_chat.py
# Módulo de Núcleo do nosso Sistema Distribuído (Nó P2P)
# ===============================================
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
            
            # Usa IP_LOCALHOST (127.0.0.1) para o setsockopt (fixa o erro inet_aton)
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
        
        # CORREÇÃO DE SINTAXE: O loop 'for' é definido corretamente em uma linha
        for no_id, (ip, porta) in list(self.peers_ativos.items()):
            if no_id != self.id: 
                try:
                    s_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s_cliente.connect((ip, porta))
                    s_cliente.sendall(msg_completa.encode('utf-8'))
                    s_cliente.close()
                except Exception as e:
                    pass 


    def processar_entrada_de_no(self, mensagem_entrada):
        """[APENAS COORDENADOR] Atribui ID e faz o Broadcast do Roster."""
        
        # Define o novo ID: Se a lista de peers não estiver vazia, pega o ID máximo + 1; senão, usa 1.
        novo_id = max(self.peers_ativos.keys()) + 1 if self.peers_ativos else 1
        
        porta_nova = mensagem_entrada['porta_unicast'] 
        ip_novo = ENDERECO_UNICAST 
            
        self.peers_ativos[novo_id] = (ip_novo, porta_nova)
        
        print(f"\n[COORDENADOR] Nó {novo_id} cadastrado em {ip_novo}:{porta_nova}")
        
        # Prepara o payload de atualização de Roster para broadcast
        roster_atualizado = {
            "tipo": "ROSTER_UPDATE",
            "peers": self.peers_ativos
        }
        payload_roster = json.dumps(roster_atualizado).encode('utf-8')

        # 1. Envia a resposta de Cadastro INICIAL ao novo nó
        resposta_cadastro = {
            "id": novo_id,
            "peers": self.peers_ativos
        }
        payload_cadastro = json.dumps(resposta_cadastro).encode('utf-8')

        try:
            s_cadastro = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s_cadastro.connect((ip_novo, porta_nova)) 
            s_cadastro.sendall(payload_cadastro)
            s_cadastro.close()
        except Exception as e:
            print(f"ERRO ao responder novo nó ({novo_id}): {e}")
            return
            
        # 2. Faz o BROADCAST (Atualização do Roster) para TODOS os nós EXISTENTES
        # CORREÇÃO DE SINTAXE: O loop 'for' é definido corretamente em uma linha
        for no_id, (ip, porta) in list(self.peers_ativos.items()):
            # Não envia para o nó recém-cadastrado e não envia para si mesmo
            if no_id != novo_id and no_id != self.id:
                try:
                    s_update = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s_update.connect((ip, porta))
                    s_update.sendall(payload_roster)
                    s_update.close()
                except Exception as e:
                    print(f"ALERTA: Falha ao enviar Roster Update ao Nó {no_id}.")


    def iniciar_no(self):
        """
        Função principal que inicia todas as threads de comunicação e o fluxo de entrada.
        """
        if not self.ativo:
            return

        # 1. Inicia as Threads Essenciais
        threading.Thread(target=self.iniciar_servidor_tcp, daemon=True).start()
        threading.Thread(target=self.iniciar_receptor_multicast, daemon=True).start()

        # 2. Lógica de Entrada e Coordenador
        if self.porta_unicast == PORTA_BASE_UNICAST:
            self.e_coordenador = True
            self.id = 1 
            self.peers_ativos[self.id] = (ENDERECO_UNICAST, self.porta_unicast) 
            print(f"\n>>>> EU SOU O COORDENADOR (ID: {self.id}) <<<<\n")
            threading.Thread(target=self.enviar_heartbeat, daemon=True).start()
        else:
            # NÓ COMUM ENTRANDO: Envia a mensagem de QUERO_ENTRAR via Multicast
            print(f"\n>>>> EU SOU UM NÓ COMUM <<<<")
            try:
                loopback_ip = socket.inet_aton(IP_LOCALHOST) 
                self.socket_multicast.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, loopback_ip)
                
                # Envia a porta UNICAST no payload JSON
                payload_entrada = json.dumps({
                    "tipo": MENSAGEM_ENTRADA,
                    "porta_unicast": self.porta_unicast
                })

                self.socket_multicast.sendto(payload_entrada.encode('utf-8'), (IP_MULTICAST, PORTA_MULTICAST))
                print(f"[STATUS] Enviado pedido de entrada via Multicast. Aguardando cadastro...")
            except Exception as e:
                print(f"[ERRO] Falha ao enviar pedido de entrada: {e}")


        # 3. Thread Principal (Entrada do Usuário)
        print("\nDigite suas mensagens. Digite /sair para encerrar.")
        
        while self.ativo:
            try:
                mensagem = input(f"[{self.id or 'AGUARDANDO ID'}@{self.porta_unicast}]> ") 
                if mensagem.lower() == '/sair':
                    self.ativo = False
                elif mensagem and self.id is not None:
                    self.enviar_mensagem_chat(mensagem)
                    
            except KeyboardInterrupt:
                self.ativo = False
            except Exception as e:
                self.ativo = False

        self.socket_tcp.close()
        print(f"Nó {self.id} encerrado.")


# ====================================================================
# EXECUTANDO O PROGRAMA
# ====================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Uso: python3 {sys.argv[0]} <porta_unicast>")
        print(f"Ex: python3 {sys.argv[0]} {PORTA_BASE_UNICAST} (para o Coordenador)")
        sys.exit(1)
    
    try:
        porta = int(sys.argv[1])
        no = NoChat(porta)
        no.iniciar_no()
        
    except ValueError:
        print("A porta deve ser um número inteiro.")
    except Exception as e:
        print(f"Ocorreu um erro fatal: {e}")
