import hashlib
import json

def calculate_md5(data: dict) -> str:
    """Gera o hash MD5 para verificação de integridade."""
    # sort_keys garante que dicionários idênticos gerem o mesmo hash
    data_string = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.md5(data_string).hexdigest()