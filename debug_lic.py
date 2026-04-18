import json, base64, re
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Leer licencia
lic = json.loads(Path('disateq.lic').read_text(encoding='utf-8'))
print('Fingerprint en lic:', lic['fingerprint'])

# Leer llave publica desde license_manager.py
contenido = Path('license_manager.py').read_text(encoding='utf-8')
match = re.search(r'_PUBLIC_KEY_PEM = """(.*?)"""', contenido, re.DOTALL)
pub_pem = match.group(1).strip()
print('Llave publica encontrada:', pub_pem[:40])

# Verificar firma
public_key = serialization.load_pem_public_key(pub_pem.encode())
firma = base64.b64decode(lic['firma'])
try:
    public_key.verify(firma, lic['payload'].encode(), padding.PKCS1v15(), hashes.SHA256())
    print('Firma OK')
except Exception as e:
    print(f'Firma INVALIDA: {e}')