import socket
import threading
import json
import time
from core.db_manager import DBManager, DataRecord
from utils.config import DDB_NODES, HEARTBEAT_INTERVAL
from utils.checksum import calculate_checksum # Assumindo que você tem uma função checksum

class NodeServer:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.host, self.port, db_uri = DDB_NODES[node_id]
        self.db_manager = DBManager(db_uri)
        self.is_active = True
        self.coordinator_id = 1 # Coordenador inicial

    def _handle_client(self, conn, addr):
        # Recebe a requisição do Middleware
        try:
            data_raw = conn.recv(4096).decode('utf-8')
            request = json.loads(data_raw)
            print(f"Nó {self.node_id}: Recebeu requisição: {request['type']}")

            # 1. Verificar Integridade (Checksum)
            if request['checksum'] != calculate_checksum(request['payload']):
                response = {"status": "ERROR", "message": "Checksum inválido."}
                conn.sendall(json.dumps(response).encode('utf-8'))
                return

            # 2. Executar Query / 2PC (Foco da Pessoa 2)
            if request['type'] == 'EXECUTE_QUERY':
                query = request['payload']['query']
                result = self.db_manager.execute_query(query)
                
                # Se for SELECT
                if isinstance(result, list): 
                    response = {
                        "status": "SUCCESS", 
                        "result": result, 
                        "executed_on": self.node_id
                    }
                else: # Se for DML (exigirá 2PC)
                    response = {"status": "PREPARED", "transaction_id": "T123"} 
            
            # ... Lógica para ELEICAO, REPLICACAO, etc ...
            
            response['checksum'] = calculate_checksum(response) # Adiciona checksum de retorno
            conn.sendall(json.dumps(response).encode('utf-8'))

        except Exception as e:
            print(f"Erro no Nó {self.node_id}: {e}")
            conn.sendall(json.dumps({"status": "ERROR", "message": str(e)}).encode('utf-8'))
        finally:
            conn.close()

    def start_server(self):
        # Inicia o servidor de sockets
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen(5)
        print(f"*** Nó DDB {self.node_id} ativo em {self.host}:{self.port} ***")

        # Inicia thread de Heartbeat (Padrão Observer/Pessoa 1)
        threading.Thread(target=self._send_heartbeats, daemon=True).start()

        while True:
            conn, addr = s.accept()
            threading.Thread(target=self._handle_client, args=(conn, addr)).start()

    def _send_heartbeats(self):
        # Envia periodicamente uma mensagem para o coordenador
        while self.is_active:
            try:
                # Na prática, se conecta ao Middleware/Coordenador
                heartbeat_msg = {
                    "type": "HEARTBEAT",
                    "sender_id": self.node_id,
                    "status": "UP"
                }
                
                # Exemplo: Enviar para o Coordenador atual (ID 1)
                # O real Coordenador escutará e manterá o status UP
                
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                print(f"Erro no heartbeat do Nó {self.node_id}: {e}")

# Ponto de entrada
if __name__ == '__main__':
    node_id = int(input("Digite o ID do Nó (1, 2, ou 3): "))
    server = NodeServer(node_id)
    server.start_server()