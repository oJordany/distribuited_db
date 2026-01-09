import sys
import threading
import time
from node.node_server import NodeServer
from utils.config import DDB_NODES

def main():
    # Validação do argumento de entrada (ID do Nó)
    if len(sys.argv) < 2:
        print("Uso correto: python main_node.py [NODE_ID]")
        print("Exemplo: python main_node.py 1")
        sys.exit(1)

    try:
        node_id = int(sys.argv[1])
    except ValueError:
        print("Erro: O NODE_ID deve ser um número inteiro.")
        sys.exit(1)

    if node_id not in DDB_NODES:
        print(f"Erro: Nó {node_id} não encontrado no arquivo de configuração (utils/config.py).")
        sys.exit(1)

    print(f"--- Iniciando Nó Distributed Database (ID: {node_id}) ---")

    # Inicializa o servidor do nó
    # A Pessoa 1 garante a infraestrutura de rede e eleição aqui
    node = NodeServer(node_id, DDB_NODES)

    try:
        # Roda o servidor (abre threads de escuta e heartbeat)
        node.run()

        # Pequeno delay para o servidor subir antes de checar eleição
        time.sleep(2)

        # Se não houver coordenador definido ao iniciar, o nó tenta verificar a rede
        # ou inicia uma eleição se detectar que os superiores estão offline.
        if node.coord_manager.coordinator_id is None:
            print(f"Nó {node_id}: Verificando estado da rede...")
            node.coord_manager.start_election()

        # Mantém a thread principal viva
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\nDesligando Nó {node_id}...")
        node.is_running = False
        sys.exit(0)
    except Exception as e:
        print(f"Erro fatal no Nó {node_id}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()