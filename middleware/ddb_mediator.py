import re
import socket
from utils.config import DDB_NODES
from core.coordinator import BullyCoordinator # Ajustado
from utils.network_helper import create_message, verify_message

class DDBMediator:
    def __init__(self, middleware_node_id):
        # O Middleware também age como um observador no Bully
        self.coordinator = BullyCoordinator(middleware_node_id, DDB_NODES)
        self.active_nodes = set(DDB_NODES.keys()) # Simplificação: assume todos ativos no início

    def handle_client_query(self, query: str):
        # Diferencia leitura de escrita para acionar o 2PC via coordenador.
        if not query:
            return {"status": "ERROR", "message": "Query vazia."}

        if self.coordinator.coordinator_id is None:
            self._discover_coordinator()

        target_node = self.coordinator.coordinator_id
        if target_node is None:
            return {"status": "ERROR", "message": "Nenhum coordenador eleito no momento."}

        if self._is_read_query(query):
            print(f"[MIDDLEWARE] Enviando query para o Coordenador: {target_node}")
            return self._send_to_node(target_node, query)

        # Escrita: coordenador executa e replica via 2PC
        print(f"[MIDDLEWARE] Enviando escrita para o Coordenador: {target_node}")
        return self._send_write(target_node, query)

    def _send_to_node(self, node_id, query):
        if node_id is None:
            return {"status": "ERROR", "message": "Nenhum nó disponível."}

        response = self._send_internal(node_id, "EXECUTE_QUERY", {"query": query})
        if not response:
            return {"status": "ERROR", "message": "Sem resposta do nó."}

        if response.get("type") == "SUCCESS":
            payload = response.get("payload", {})
            return {
                "status": "SUCCESS",
                "result": payload.get("result"),
                "executed_on_node": node_id,
            }

        payload = response.get("payload", {})
        return {
            "status": "ERROR",
            "message": payload.get("message", f"Resposta inesperada: {response.get('type')}"),
        }

    def _send_write(self, node_id, query):
        response = self._send_internal(node_id, "EXECUTE_2PC", {"query": query})
        if not response:
            return {"status": "ERROR", "message": "Sem resposta do nó."}

        payload = response.get("payload", {})
        if response.get("type") == "TX_RESULT":
            status = payload.get("status")
            if status == "SUCCESS":
                return {
                    "status": "SUCCESS",
                    "message": payload.get("message"),
                    "executed_on_node": node_id,
                }
            return {
                "status": "ERROR",
                "message": payload.get("message", "Falha na transacao."),
            }

        return {
            "status": "ERROR",
            "message": payload.get("message", f"Resposta inesperada: {response.get('type')}"),
        }

    def _discover_coordinator(self):
        for node_id in sorted(DDB_NODES.keys()):
            response = self._send_internal(node_id, "GET_COORDINATOR", {})
            if not response:
                continue
            if response.get("type") != "COORDINATOR_INFO":
                continue
            coord_id = response.get("payload", {}).get("coordinator_id")
            if coord_id is not None:
                self.coordinator.coordinator_id = coord_id
                return coord_id
        return None

    def _send_internal(self, node_id, msg_type, payload):
        host, port, _ = DDB_NODES[node_id]
        try:
            with socket.create_connection((host, port), timeout=5) as s:
                msg = create_message(msg_type, payload)
                s.sendall(msg.encode())
                resp_raw = s.recv(4096).decode()
                return verify_message(resp_raw) if resp_raw else None
        except Exception as e:
            return {"type": "ERROR", "payload": {"message": str(e)}}

    def _is_read_query(self, query: str) -> bool:
        keyword = self._first_keyword(query)
        return keyword in {"SELECT", "SHOW", "DESCRIBE", "EXPLAIN"}

    def _first_keyword(self, query: str) -> str:
        text = query.strip()
        while True:
            if text.startswith("--"):
                newline_idx = text.find("\n")
                if newline_idx == -1:
                    return ""
                text = text[newline_idx + 1:].lstrip()
                continue
            if text.startswith("/*"):
                end_idx = text.find("*/")
                if end_idx == -1:
                    return ""
                text = text[end_idx + 2:].lstrip()
                continue
            break
        match = re.match(r"([A-Za-z]+)", text)
        return match.group(1).upper() if match else ""
