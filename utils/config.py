# Estrutura de Nó: {ID: (IP, Porta, DB_URI)}
DDB_NODES = {
    1: ('127.0.0.1', 8001, 'mysql+mysqlconnector://ddb_user:ddb_pass@127.0.0.1:3306/ddb_node_1'),
    2: ('127.0.0.1', 8002, 'mysql+mysqlconnector://ddb_user:ddb_pass@127.0.0.1:3307/ddb_node_2'),
    3: ('127.0.0.1', 8003, 'mysql+mysqlconnector://ddb_user:ddb_pass@127.0.0.1:3308/ddb_node_3'),
}

MIDDLEWARE_HOST = '127.0.0.1'
MIDDLEWARE_PORT = 9000
HEARTBEAT_INTERVAL = 5 # Segundos
