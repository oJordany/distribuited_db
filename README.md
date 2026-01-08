# Sistema de Banco de Dados Distribuído

Este projeto é um sistema de banco de dados distribuído desenvolvido em Python, projetado para garantir a consistência dos dados em múltiplos nós através do protocolo Two-Phase Commit (2PC) e para fornecer tolerância a falhas usando o algoritmo de eleição Bully para seleção do coordenador.

## Arquitetura

O sistema é composto por três componentes principais:

*   **Nós (`main_node.py`):** São os componentes que armazenam os dados, cada um conectado ao seu próprio banco de dados MySQL. Eles atuam como participantes nos protocolos 2PC e de eleição.
*   **Middleware (`main_middleware.py`):** Um servidor central que recebe consultas de um cliente. Ele atua como o coordenador da transação, iniciando o protocolo 2PC para operações de escrita.
*   **Cliente (`client_app.py`):** Uma aplicação de linha de comando para enviar consultas SQL ao middleware.

## Como Executar

### Pré-requisitos

1.  Instale as dependências necessárias:
    ```bash
    pip install -r requirements.txt
    ```
2.  Configure três bancos de dados MySQL separados, conforme definido em `utils/config.py` (por exemplo, `db_node_1`, `db_node_2`, `db_node_3`).

### Execução

1.  **Iniciar os Nós:** Abra três terminais separados e execute um nó em cada um:
    ```bash
    python main_node.py 1
    ```
    ```bash
    python main_node.py 2
    ```
    ```bash
    python main_node.py 3
    ```
    Os nós realizarão automaticamente uma eleição para escolher um coordenador.

2.  **Iniciar o Middleware:** Em outro terminal, execute:
    ```bash
    python main_middleware.py
    ```

3.  **Executar o Cliente:** Em um último terminal, use a aplicação cliente para enviar consultas SQL:
    ```bash
    python client_app.py
    ```

## Falha Crítica

O projeto possui um bug importante que o impede de funcionar conforme o planejado. O `DDBMediator` no middleware está incompleto. Ele envia todas as consultas (incluindo `INSERT`, `UPDATE`, `DELETE`) para o coordenador como consultas de leitura simples e não replicadas (`EXECUTE_QUERY`). **Falha em chamar o método `execute_distributed_transaction`** disponível em `core/coordinator.py`, que implementa corretamente o protocolo 2PC.

Para corrigir o projeto, o método `DDBMediator.handle_client_query` deve ser atualizado para analisar a consulta SQL. Se a consulta for uma operação de escrita, ele deve chamar `self.coordinator.execute_distributed_transaction(query)`. Se for uma leitura, ele pode manter o comportamento atual. Sem essa correção, o banco de dados não replicará nenhuma escrita, frustrando seu objetivo principal.

