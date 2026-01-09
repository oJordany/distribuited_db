from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ReplicationLog(Base):
    __tablename__ = 'replication_logs'
    id = Column(Integer, primary_key=True)
    query_text = Column(String(500))
    status = Column(String(50))
    executed_at = Column(DateTime, default=datetime.utcnow)
