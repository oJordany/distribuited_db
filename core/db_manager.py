from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DataRecord(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    content = Column(String(255))

class DBManager:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
        Base.metadata.create_all(self.engine) # Cria a tabela se não existir
        self.Session = sessionmaker(bind=self.engine)

    def execute_query(self, query: str):
        # Implementação simplificada para SELECT
        session = self.Session()
        try:
            if query.upper().startswith("SELECT"):
                # Exemplo: session.execute(text(query)).fetchall()
                print(f"DEBUG: Executando SELECT: {query}")
                return [{"id": 1, "content": "Dados simulados"}]
            
            # Para INSERT/UPDATE/DELETE, exige lógica de 2PC
            # Retorna o objeto Session para uso no 2PC
            return session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            # Não fechar a sessão se for para 2PC
            if query.upper().startswith("SELECT"):
                session.close()

    # Métodos para 2PC (prepare, commit, rollback) seriam adicionados aqui...