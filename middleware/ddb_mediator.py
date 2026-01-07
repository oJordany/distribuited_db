import json
import socket
import itertools
from utils.config import DDB_NODES
from core.coordinator import BullyCoordinator # Ajustado
from middleware.load_balancer import LoadBalancer
from utils.network_helper import create_message, verify_message

class DDBMediator:
    def __init__(self, middleware_node_id):
        # O Middleware também age como um observador no Bully
        self.coordinator = BullyCoordinator(middleware_node_id, DDB_NODES)
        self.load_balancer = LoadBalancer(list(DDB_NODES.keys()))
        self.active_nodes = set(DDB_NODES.keys()) # Simplificação: assume todos ativos no início

    def handle_client_query(self, query: str):
        query_upper = query.upper().strip()
        
        # Determinar se é Leitura ou Escrita
        if query_upper.startswith("SELECT"):
            # Usa Load Balancer para distribuir leituras
            target_node = self.load_balancer.get_next_node(self.active_nodes)
            return self._send_to_node(target_node, query)
        else:
            # Escrita: Deve ser enviada para o Coordenador atual (Replicação)
            target_node = self.coordinator.coordinator_id
            print(f"Encaminhando escrita para o Coordenador: {target_node}")
            return self._send_to_node(target_node, query)

    def _send_to_node(self, node_id, query):
        if node_id is None:
            return {"status": "ERROR", "message": "Nenhum nó disponível."}
        
        host, port, _ = DDB_NODES[node_id]
        try:
            with socket.create_connection((host, port), timeout=5) as s:
                msg = create_message("EXECUTE_QUERY", {"query": query})
                s.sendall(msg.encode())
                
                resp_raw = s.recv(4096).decode()
                response = verify_message(resp_raw)
                response['executed_on_node'] = node_id
                return response
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}