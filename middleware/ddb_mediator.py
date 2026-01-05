# middleware/ddb_mediator.py

import json
import socket
from utils.config import DDB_NODES, MIDDLEWARE_HOST, MIDDLEWARE_PORT
from core.coordinator import Coordinator
from middleware.load_balancer import LoadBalancer # Assumindo uma classe LoadBalancer
import itertools

class DDBMediator:
    def __init__(self):
        # O coordenador gerencia o estado dos nós e a eleição
        self.coordinator = Coordinator(DDB_NODES)
        
        # O Load Balancer distribui as requisições SELECT
        # Usaremos o itertools.cycle para um Round Robin simples
        self.load_balancer = itertools.cycle(DDB_NODES.keys()) 

    def _forward_request_to_node(self, node_id: int, request_payload: dict):
        # Lógica de socket simples para enviar requisição a um nó específico
        host, port, _ = DDB_NODES[node_id]
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            
            # Monta a requisição final para o Nó
            final_request = {
                "type": "EXECUTE_QUERY",
                "payload": request_payload,
                "checksum": "XYZ" # Calcular o checksum real
            }
            
            s.sendall(json.dumps(final_request).encode('utf-8'))
            
            # Recebe a resposta do Nó
            response_raw = s.recv(4096).decode('utf-8')
            return json.loads(response_raw)
        
        except Exception as e:
            # Marca o nó como DOWN e dispara eleição/notificação
            print(f"Falha de comunicação com o Nó {node_id}: {e}")
            self.coordinator.mark_node_down(node_id)
            return {"status": "ERROR", "message": f"Nó {node_id} inativo ou inacessível."}
        finally:
            s.close()


    def handle_client_query(self, query: str):
        query_type = query.upper().split(' ')[0]

        if query_type == 'SELECT':
            # 1. Balanceamento de Carga (Round Robin)
            available_nodes = self.coordinator.get_active_nodes()
            
            if not available_nodes:
                 return {"status": "ERROR", "message": "Nenhum nó ativo disponível."}
            
            # Escolhe o próximo nó ativo
            selected_node = next(self.load_balancer)
            while selected_node not in available_nodes:
                 selected_node = next(self.load_balancer) # Pula para o próximo ativo

            # 2. Encaminha a query
            request_payload = {"query": query}
            response = self._forward_request_to_node(selected_node, request_payload)
            
            # Adiciona o nó que executou ao retorno final
            response['executed_on_node'] = selected_node 
            return response
            
        elif query_type in ('INSERT', 'UPDATE', 'DELETE'):
            # 3. Transação Distribuída (2PC)
            # Este é o ponto onde o Middleware delega ao Coordinator a execução do 2PC
            print("Iniciando Transação Distribuída (2PC)...")
            return self.coordinator.execute_2pc(query)
            
        else:
            return {"status": "ERROR", "message": "Tipo de query não suportado."}