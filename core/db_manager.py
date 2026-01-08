from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import date, datetime, time
from decimal import Decimal

class DBManager:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        # Dicionário para manter sessões abertas aguardando o 2PC
        self.active_transactions = {}

    def execute_select(self, query: str):
        """Executa consultas de leitura imediatamente."""
        session = self.Session()
        try:
            result = session.execute(text(query))
            rows = []
            for row in result:
                row_dict = dict(row._mapping)
                rows.append({k: self._jsonify_value(v) for k, v in row_dict.items()})
            return rows
        except Exception as e:
            print(f"Erro no SELECT: {e}")
            return None
        finally:
            session.close()

    def prepare(self, query: str):
        """
        FASE 1: Executa a query mas não commita. 
        Retorna um transaction_id para referência futura.
        """
        session = self.Session()
        try:
            # Inicia a transação e executa a query DML
            session.execute(text(query))
            # Gera um ID único para esta transação distribuída
            tid = str(uuid.uuid4())
            self.active_transactions[tid] = session
            print(f"[2PC-PREPARE] Transação {tid} preparada com sucesso.")
            return tid
        except Exception as e:
            session.rollback()
            session.close()
            print(f"[2PC-PREPARE] Falha ao preparar query: {e}")
            return None

    def commit(self, tid: str):
        """FASE 2: Efetiva a transação no banco de dados."""
        session = self.active_transactions.get(tid)
        if session:
            try:
                session.commit()
                print(f"[2PC-COMMIT] Transação {tid} efetivada.")
                return True
            except Exception as e:
                print(f"[2PC-COMMIT] Erro ao commitar {tid}: {e}")
                return False
            finally:
                session.close()
                del self.active_transactions[tid]
        return False

    def rollback(self, tid: str):
        """FASE 2 (Erro): Desfaz as alterações da transação."""
        session = self.active_transactions.get(tid)
        if session:
            try:
                session.rollback()
                print(f"[2PC-ROLLBACK] Transação {tid} desfeita.")
                return True
            finally:
                session.close()
                del self.active_transactions[tid]
        return False

    def _jsonify_value(self, value):
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, Decimal):
            return float(value)
        return value
