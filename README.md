# 🧩 DDB Middleware - Banco Distribuido

<p align="center">
  <font size="7">🧩</font> <font size="7">🗃️</font> <font size="7">🔗</font>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white" alt="Python Version">
  <img src="https://img.shields.io/badge/Protocol-Bully%20%7C%202PC-orange" alt="Bully | 2PC">
  <img src="https://img.shields.io/badge/Transport-TCP-green" alt="TCP">
  <img src="https://img.shields.io/badge/GUI-Tkinter-yellow" alt="Tkinter">
  <img src="https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql&logoColor=white" alt="MySQL">
</p>

Middleware e nos para um banco de dados distribuido com eleicao Bully e suporte a 2PC. Inclui um cliente grafico para enviar consultas SQL via TCP.

## Contexto do projeto
Projeto da disciplina Laboratorio de Sistemas Distribuidos.

Alunos:
- Luiz Jordany de Sousa Silva
- Ivan Luis Gama Grana
- Syanne Karoline Moreira Tavares

## Visao geral
- Cliente envia SQL ao middleware via socket TCP.
- Middleware descobre o coordenador e encaminha todas as queries a ele.
- Coordenador executa leituras e replica escritas via 2PC.
- Eleicao Bully e heartbeat mantem um coordenador ativo.

## Como executar
1. Ajuste os enderecos, portas e URIs dos bancos em `utils/config.py`.
2. Instale as dependencias:

```bash
python -m pip install -r requirements.txt
```

3. Em terminais separados, suba cada no:

```bash
python main_node.py 1
python main_node.py 2
python main_node.py 3
```

4. Inicie o middleware:

```bash
python main_middleware.py
```

5. Abra o cliente grafico:

```bash
python client/client_app.py
```

## Fluxo de funcionamento
O cliente envia uma query ao middleware, que utiliza o `DDBMediator` para descobrir o coordenador e encaminhar a solicitacao. Todas as consultas vao para o coordenador: leituras usam `EXECUTE_QUERY`, e escritas usam `EXECUTE_2PC`, com replicacao via `PREPARE`/`COMMIT`/`ROLLBACK`. Os nos enviam heartbeat periodico para detectar falhas e disparar eleicao Bully quando necessario.

## Estrutura de modulos

## Top-level
- `main_middleware.py`: inicia o servidor TCP do middleware.
- `main_node.py`: inicia um no especifico e valida o `NODE_ID`.
- `requirements.txt`: dependencias Python do projeto.
- `README.md`: documentacao e instrucoes de uso.

## client/
- `client/client_app.py`: interface Tkinter para enviar SQL e exibir respostas.
- `client/__init__.py`: marca o pacote do cliente.

## middleware/
- `middleware/request_handler.py`: servidor TCP que recebe requisicoes do cliente e delega ao mediator.
- `middleware/ddb_mediator.py`: roteia queries para o no coordenador usando o protocolo de rede.
- `middleware/__init__.py`: marca o pacote do middleware.

## core/
- `core/coordinator.py`: eleicao Bully, notificacao de coordenador e logica de 2PC.
- `core/db_manager.py`: execucao de SELECT e gerenciamento de transacoes para 2PC.
- `core/network_protocol.py`: constantes com tipos de mensagens e status.
- `core/__init__.py`: marca o pacote core.

## node/
- `node/node_server.py`: servidor do no, trata mensagens de eleicao, heartbeat e 2PC.
- `node/replication_log.py`: modelo SQLAlchemy de log (depende de uma Base declarativa).
- `node/__init__.py`: marca o pacote do no.

## utils/
- `utils/config.py`: configuracao de host, portas e URIs dos bancos por no.
- `utils/network_helper.py`: empacota e valida mensagens com checksum.
- `utils/checksum.py`: utilitario de MD5 (nao usado no fluxo principal).
- `utils/__init__.py`: marca o pacote utils.

## tests/
- `tests/sample_queries.sql`: exemplo de schema e queries para copiar e colar no cliente.

## Configuracao
Edite `utils/config.py` para apontar cada no para seu banco MySQL. Cada entrada em `DDB_NODES` segue o formato `(IP, Porta, DB_URI)`.
Obs: a porta e do servidor do no, enquanto a porta do MySQL fica dentro da `DB_URI`.

### Execucao em 3 PCs (laboratorio)
- Cada PC roda 1 no e 1 banco local.
- Em `utils/config.py`, cada no deve usar o IP real do PC onde o banco esta rodando.
- Suba `main_node.py` no respectivo PC com o `NODE_ID` correto.
- O middleware pode rodar em qualquer PC, mas deve conseguir acessar os 3 nos pela rede.

### Execucao local com Docker Compose (simula 3 PCs)
Para testes locais, use 3 bancos MySQL em containers separados. O compose abaixo sobe:
- `db_node_1` na porta 3306
- `db_node_2` na porta 3307
- `db_node_3` na porta 3308

Suba os containers:

```bash
docker compose up -d
```

Para parar e remover:

```bash
docker compose down
```

Atualize `utils/config.py` para usar as portas locais acima, por exemplo:

```python
DDB_NODES = {
    1: ('127.0.0.1', 8001, 'mysql+mysqlconnector://ddb_user:ddb_pass@127.0.0.1:3306/ddb_node_1'),
    2: ('127.0.0.1', 8002, 'mysql+mysqlconnector://ddb_user:ddb_pass@127.0.0.1:3307/ddb_node_2'),
    3: ('127.0.0.1', 8003, 'mysql+mysqlconnector://ddb_user:ddb_pass@127.0.0.1:3308/ddb_node_3'),
}
```

## Protocolo de rede
As mensagens sao JSON com `type`, `payload` e `checksum`. O checksum usa MD5 do payload para validar integridade. Tipos principais: `ELECTION`, `ANSWER`, `COORDINATOR_VICTORY`, `HEARTBEAT`, `GET_COORDINATOR`, `COORDINATOR_INFO`, `EXECUTE_QUERY`, `EXECUTE_2PC`, `TX_RESULT`, `PREPARE`, `COMMIT`, `ROLLBACK`.

## Observacoes
Se o middleware retornar "Nenhum coordenador eleito", os nos nao reportaram um lider ativo. Verifique se algum no completou a eleicao e se as portas estao acessiveis.
- O middleware descobre o coordenador consultando os nos com `GET_COORDINATOR`.
- Escritas sao executadas no coordenador via `EXECUTE_2PC` e replicadas com 2PC.
- Os nos registram um log de replicacao na tabela `replication_logs` com status das transacoes.

## Consultas de exemplo
O arquivo `tests/sample_queries.sql` inclui comandos para criar tabela, inserir dados, atualizar, remover, consultar e ver os logs de replicacao. Para consultar os logs diretamente:

```sql
SELECT id, query_text, status, executed_at
FROM replication_logs
ORDER BY executed_at DESC;
```
