import socket
import json
from utils.config import MIDDLEWARE_HOST, MIDDLEWARE_PORT

def run_client():
    print("--- Console do Banco de Dados Distribuído ---")
    while True:
        query = input("\nDigite sua SQL query (ou 'sair'): ")
        if query.lower() == 'sair': break

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((MIDDLEWARE_HOST, MIDDLEWARE_PORT))
                # Envia a query para o Middleware
                s.sendall(json.dumps({"query": query}).encode())
                
                # Recebe a resposta
                data = s.recv(4096).decode()
                response = json.loads(data)
                
                if response.get("status") == "SUCCESS":
                    print(f"Resultado (Nó {response.get('executed_on_node')}): {response.get('result')}")
                else:
                    print(f"Erro: {response.get('message')}")
        except Exception as e:
            print(f"Erro ao conectar ao Middleware: {e}")

if __name__ == "__main__":
    run_client()