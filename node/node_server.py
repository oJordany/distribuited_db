import socket
import threading
import time
from utils.network_helper import verify_message, create_message
from core.coordinator import BullyCoordinator
from core.db_manager import DBManager

class NodeServer:
    def __init__(self, node_id, nodes_config):
        self.node_id = node_id
        self.config = nodes_config[node_id]
        self.all_configs = nodes_config
        self.coord_manager = BullyCoordinator(node_id, nodes_config) 
        self.is_running = True
        self.db_manager = DBManager(self.config[2])
        self._startup_error = None
        self._listen_ready = threading.Event() # obj de sincronização entre threads

    def run(self):
        # Thread para escutar conexões
        self._startup_error = None
        self._listen_ready.clear()
        server_thread = threading.Thread(target=self._listen)
        server_thread.start()
        self._listen_ready.wait(timeout=2) # espera até a thread de escuta estar pronta
        if self._startup_error:
            self.is_running = False
            raise self._startup_error

        # Thread para Heartbeat 
        threading.Thread(target=self._heartbeat_sender, daemon=True).start()

    def _listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # configurando opções do socket -> evita erro de porta em uso quando a porta é reutilizada após fechar e abrir rápido
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", self.config[1])) # associa socket a endereço local para escuta
            except OSError:
                self._startup_error = RuntimeError(
                    f"Porta {self.config[1]} ja em uso. Pare outro processo ou mude a porta em utils/config.py."
                )
                self._listen_ready.set()
                return
            s.listen()
            self._listen_ready.set()
            print(f"Nó {self.node_id} ouvindo em {self.config[1]}...")
            
            while self.is_running:
                conn, addr = s.accept()
                threading.Thread(target=self._handle_connection, args=(conn,)).start()

    def _handle_connection(self, conn):
        with conn:
            try:
                # Recebe e valida a mensagem usando o Checksum
                raw_data = conn.recv(4096).decode() # decode() para string
                if not raw_data:
                    return
                
                data = verify_message(raw_data)
                m_type = data['type']
                payload = data['payload']

                # ==========================================
                # Eleição e Bully
                # ==========================================
                if m_type == "ELECTION":
                    # Se um nó menor inicia eleição, respondemos OK e iniciamos a nossa eleição
                    conn.sendall(create_message("ANSWER", {"status": "OK"}).encode())
                    threading.Thread(target=self.coord_manager.start_election).start()

                elif m_type == "COORDINATOR_VICTORY":
                    # Um novo líder se proclamou
                    self.coord_manager.coordinator_id = payload['leader']
                    self.coord_manager.is_electing = False
                    print(f"[REDE] Novo Coordenador reconhecido: {payload['leader']}")

                elif m_type == "HEARTBEAT":
                    # Respondemos ao batimento cardíaco para confirmar que estamos vivos
                    conn.sendall(create_message("ACK", {"status": "alive"}).encode())

                elif m_type == "GET_COORDINATOR":
                    # Informa quem o nó entende como coordenador atual
                    conn.sendall(
                        create_message(
                            "COORDINATOR_INFO",
                            {"coordinator_id": self.coord_manager.coordinator_id},
                        ).encode()
                    )

                # ==========================================
                # Transações e 2PC
                # ==========================================
                elif m_type == "PREPARE":
                    tid = self.db_manager.prepare(payload['query'])
                    status = "PREPARED" if tid else "FAIL"
                    conn.sendall(create_message("ACK", {"status": status, "tid": tid}).encode())

                elif m_type == "COMMIT":
                    success = self.db_manager.commit(payload['tid'])
                    conn.sendall(create_message("ACK", {"status": "SUCCESS" if success else "FAIL"}).encode())

                elif m_type == "ROLLBACK":
                    self.db_manager.rollback(payload['tid'])
                    conn.sendall(create_message("ACK", {"status": "ROLLED_BACK"}).encode())

                # ==========================================
                # Middleware
                # ==========================================
                elif m_type == "EXECUTE_QUERY":
                    result = self.db_manager.execute_select(payload['query'])
                    conn.sendall(create_message("SUCCESS", {"result": result}).encode())

                elif m_type == "EXECUTE_2PC":
                    if (
                        self.coord_manager.coordinator_id is not None
                        and self.coord_manager.coordinator_id != self.node_id
                    ):
                        conn.sendall(
                            create_message(
                                "TX_RESULT",
                                {"status": "FAIL", "message": "Este nó não é o coordenador."},
                            ).encode()
                        )
                    else:
                        result = self.coord_manager.execute_distributed_transaction(payload.get("query", ""))
                        status = "SUCCESS" if result.get("status") == "SUCCESS" else "FAIL"
                        conn.sendall(
                            create_message(
                                "TX_RESULT",
                                {"status": status, "message": result.get("message")},
                            ).encode()
                        )

            except Exception as e:
                print(f"[ERRO] Falha no processamento da mensagem: {e}")


    def _heartbeat_sender(self):
        """Informa periodicamente que o nó está ativo enviando para o coordenador."""
        while self.is_running:
            time.sleep(5)
            target_id = self.coord_manager.coordinator_id
            if target_id == self.node_id: continue # Sou o coordenador, não preciso me avisar

            host, port, _ = self.all_configs[target_id]
            try:
                with socket.create_connection((host, port), timeout=2) as s:
                    s.sendall(create_message('HEARTBEAT', {'node': self.node_id}).encode())
            except:
                print(f"Coordenador {target_id} não respondeu!")
                self.coord_manager.start_election() # Inicia eleição se o coordenador falhar
