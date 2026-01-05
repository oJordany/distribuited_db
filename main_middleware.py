from middleware.ddb_mediator import DDBMediator

if __name__ == '__main__':
    mediator = DDBMediator()

    # Simula o cliente se conectando ao middleware
    print("Middleware DDB ativo (simulação de escuta na porta 9000)...")

    # Teste de SELECT (Round Robin)
    for i in range(5):
         result = mediator.handle_client_query("SELECT * FROM records WHERE id = 1")
         print(f"Resultado {i+1}: {result}")

    # Teste de DML (2PC)
    result_dml = mediator.handle_client_query("INSERT INTO records (content) VALUES ('novo registro')")
    print(f"Resultado DML: {result_dml}")