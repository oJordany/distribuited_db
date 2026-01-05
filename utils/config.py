# Estrutura de Nó: {ID: (IP, Porta, DB_URI)}
DDB_NODES = {
    1: ('127.0.0.1', 8001, 'mysql+mysqlconnector://user:pass@localhost:3306/db_node_1'),
    2: ('127.0.0.1', 8002, 'mysql+mysqlconnector://user:pass@localhost:3306/db_node_2'),
    3: ('127.0.0.1', 8003, 'mysql+mysqlconnector://user:pass@localhost:3306/db_node_3'),
}

MIDDLEWARE_HOST = '127.0.0.1'
MIDDLEWARE_PORT = 9000
HEARTBEAT_INTERVAL = 5 # Segundos