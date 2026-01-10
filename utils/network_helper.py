import hashlib
import json

def calculate_checksum(data: dict) -> str:
    """Gera um hash MD5 do conteúdo da mensagem (excluindo o campo checksum)."""
    # Ordenamos as chaves para garantir que o hash seja consistente
    dump = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.md5(dump).hexdigest() # calcula hash MD5 desses bytes e retorna como txt hexadecimal

def create_message(msg_type: str, payload: dict) -> str:
    """Cria o envelope da mensagem seguindo o protocolo definido."""
    message = {
        "type": msg_type,
        "payload": payload
    }
    message["checksum"] = calculate_checksum(payload)
    return json.dumps(message)

def verify_message(raw_data: str) -> dict:
    """Decodifica e valida a integridade da mensagem recebida."""
    data = json.loads(raw_data)
    expected_checksum = calculate_checksum(data['payload'])
    
    if data['checksum'] != expected_checksum:
        raise ValueError("Erro de Integridade: Checksum não confere!")
    return data