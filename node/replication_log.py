import datetime

class ReplicationLog:
    def __init__(self):
        self.logs = []

    def add_entry(self, query, status="PENDING"):
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "query": query,
            "status": status
        }
        self.logs.append(entry)
        print(f"[LOG] Operação registrada: {query}")
        return entry