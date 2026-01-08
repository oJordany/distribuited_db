from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class ReplicationLog(Base):
    __tablename__ = 'replication_logs'
    id = Column(Integer, primary_key=True)
    query_text = Column(String(500))
    status = Column(String(50))
    executed_at = Column(DateTime, default=datetime.utcnow)