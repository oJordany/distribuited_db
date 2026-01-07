import itertools

class LoadBalancer:
    def __init__(self, node_ids):
        self.node_ids = node_ids
        self.cycle = itertools.cycle(node_ids)

    def get_next_node(self, active_nodes):
        """Retorna o próximo nó disponível usando Round Robin."""
        if not active_nodes:
            return None
        
        # Tenta encontrar o próximo nó do ciclo que esteja ativo
        for _ in range(len(self.node_ids)):
            target = next(self.cycle)
            if target in active_nodes:
                return target
        return None