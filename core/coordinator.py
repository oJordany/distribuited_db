import socket
import threading
import time
from utils.network_helper import create_message, verify_message

class BullyCoordinator:
    def __init__(self, node_id, nodes_config):
        self.node_id = node_id
        self.nodes_config = nodes_config
        self.coordinator_id = None
        self.is_electing = False
        self.lock = threading.Lock()

    def start_election(self):
        """Fase 1: Envia ELECTION para todos os nós com ID maior."""
        with self.lock:
            if self.is_electing: return
            self.is_electing = True
        
        print(f"[ELEIÇÃO] Nó {self.node_id} detectou falha e iniciou eleição.")
        
        higher_nodes = [nid for nid in self.nodes_config.keys() if nid > self.node_id]
        
        if not higher_nodes:
            self.proclaim_victory()
            return

        any_response = False
        for nid in higher_nodes:
            response = self._send_to_node(nid, "ELECTION", {"sender": self.node_id})
            if response and response.get("type") == "ANSWER" and response.get("payload", {}).get("status") == "OK":
                any_response = True
        
        if not any_response:
            self.proclaim_victory()
        else:
            # Aguarda um tempo para o nó superior proclamar vitória. 
            # Se não houver resposta em X segundos, reinicia.
            threading.Timer(10.0, self._check_if_leader_elected).start()

    def proclaim_victory(self):
        """Fase 3: O nó se torna o novo Coordenador e avisa a todos."""
        self.coordinator_id = self.node_id
        self.is_electing = False
        print(f"[VITÓRIA] Nó {self.node_id} é o novo coordenador!")
        
        for nid in self.nodes_config.keys():
            if nid != self.node_id:
                self._send_to_node(nid, "COORDINATOR_VICTORY", {"leader": self.node_id})

    def _send_to_node(self, target_id, msg_type, payload):
        """Helper para envio via Sockets."""
        host, port, _ = self.nodes_config[target_id]
        try:
            with socket.create_connection((host, port), timeout=5) as s:
                s.sendall(create_message(msg_type, payload).encode())
                raw = s.recv(1024).decode()
                return verify_message(raw) if raw else None
        except:
            return None

    def _check_if_leader_elected(self):
        if self.is_electing:
            print(f"[RE-ELECTION] Ninguém assumiu, {self.node_id} reiniciando...")
            self.is_electing = False
            self.start_election()

    def execute_distributed_transaction(self, query):
        """
        Executa o protocolo Two-Phase Commit (2PC).
        """
        print(f"[2PC] Iniciando transação distribuída: {query}")
        prepared_nodes = {} # {node_id: tid}

        # --- FASE 1: PREPARE ---
        for nid in self.nodes_config.keys():
            # Envia PREPARE para todos os nós (inclusive ele mesmo)
            resp = self._send_to_node(nid, "PREPARE", {"query": query})

            payload = resp.get("payload", {}) if resp else {}
            if resp and payload.get("status") == "PREPARED":
                prepared_nodes[nid] = payload.get("tid")
                print(f"[2PC] Nó {nid} está PREPARADO.")
            else:
                print(f"[2PC] Nó {nid} FALHOU no prepare. Abortando tudo...")
                self._rollback_all(prepared_nodes)
                return {"status": "FAIL", "message": f"Nó {nid} falhou no prepare."}

        # --- FASE 2: COMMIT ---
        print("[2PC] Todos os nós preparados. Enviando COMMIT...")
        for nid, tid in prepared_nodes.items():
            self._send_to_node(nid, "COMMIT", {"tid": tid})
        
        return {"status": "SUCCESS", "message": "Transação commitada em todos os nós."}

    def _rollback_all(self, prepared_nodes):
        """Cancela a transação nos nós que já tinham dado OK."""
        for nid, tid in prepared_nodes.items():
            self._send_to_node(nid, "ROLLBACK", {"tid": tid})
