import socket
import json
import threading
from middleware.ddb_mediator import DDBMediator

class RequestHandler:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.mediator = DDBMediator(middleware_node_id=99) # ID fictício para o middleware
        self.is_running = True

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            print(f"[*] Request Handler ouvindo na porta {self.port} para Clientes...")
            
            while self.is_running:
                conn, addr = s.accept()
                client_thread = threading.Thread(target=self._handle_client, args=(conn,))
                client_thread.start()

    def _handle_client(self, conn):
        try:
            data = conn.recv(4096).decode()
            if not data: return
            
            request = json.loads(data)
            query = request.get("query")
            
            # Chama o Mediator para processar a query (Pessoa 3)
            response = self.mediator.handle_client_query(query)
            
            conn.sendall(json.dumps(response).encode())
        except Exception as e:
            error_resp = {"status": "ERROR", "message": f"Erro no Handler: {str(e)}"}
            conn.sendall(json.dumps(error_resp).encode())
        finally:
            conn.close()