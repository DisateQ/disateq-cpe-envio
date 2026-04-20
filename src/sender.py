"""
sender.py
=========
Envío de comprobantes a APIFAS (real o mock) — Motor CPE DisateQ™ v3.0

Soporta dos modos:
- MOCK: Simulación local sin internet (para pruebas)
- REAL: Envío real a APIFAS producción
"""

import json
import requests
from pathlib import Path
from typing import Dict, Tuple
from datetime import datetime


class APISender:
    """
    Envía archivos TXT a APIFAS (real o mock).
    """
    
    def __init__(self, mode: str = "mock", url: str = None, usuario: str = None, token: str = None):
        """
        Inicializa sender.
        
        Args:
            mode: "mock" o "real"
            url: URL de APIFAS (solo para mode=real)
            usuario: Usuario APIFAS (solo para mode=real)
            token: Token APIFAS (solo para mode=real)
        """
        self.mode = mode.lower()
        self.url = url
        self.usuario = usuario
        self.token = token
        
        if self.mode == "real" and not all([url, usuario, token]):
            raise ValueError("Modo 'real' requiere url, usuario y token")
    
    def enviar(self, txt_filepath: str) -> Tuple[bool, Dict]:
        """
        Envía archivo TXT a APIFAS.
        
        Args:
            txt_filepath: Ruta al archivo .txt generado
        
        Returns:
            (exito, respuesta_dict)
        """
        if self.mode == "mock":
            return self._enviar_mock(txt_filepath)
        else:
            return self._enviar_real(txt_filepath)
    
    def _enviar_mock(self, txt_filepath: str) -> Tuple[bool, Dict]:
        """
        Simula envío a APIFAS (sin conexión real).
        
        Genera respuesta simulada tipo CDR.
        """
        print(f"   📤 [MOCK] Enviando: {Path(txt_filepath).name}")
        
        # Leer contenido del archivo
        with open(txt_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer serie-numero del archivo
        filename = Path(txt_filepath).stem  # B001-00000001
        
        # Simular respuesta exitosa
        respuesta = {
            "estado": "OK",
            "codigo_respuesta": "0",
            "mensaje": "Comprobante aceptado por SUNAT",
            "comprobante": filename,
            "fecha_proceso": datetime.now().isoformat(),
            "hash_cpe": "abc123def456",
            "cdr": {
                "codigo_sunat": "0",
                "descripcion_sunat": "La Factura numero F001-00000001, ha sido aceptada",
                "notas": []
            },
            "modo": "MOCK"
        }
        
        print(f"   ✅ [MOCK] Respuesta: {respuesta['mensaje']}")
        
        return True, respuesta
    
    def _enviar_real(self, txt_filepath: str) -> Tuple[bool, Dict]:
        """
        Envía archivo TXT a APIFAS producción.
        
        POST multipart/form-data:
        - file: archivo .txt
        - usuario: usuario APIFAS
        - token: token APIFAS
        """
        print(f"   📤 [REAL] Enviando a: {self.url}")
        
        try:
            # Leer archivo
            with open(txt_filepath, 'rb') as f:
                files = {'file': (Path(txt_filepath).name, f, 'text/plain')}
                
                data = {
                    'usuario': self.usuario,
                    'token': self.token
                }
                
                # Enviar POST
                response = requests.post(
                    self.url,
                    files=files,
                    data=data,
                    timeout=30
                )
            
            # Procesar respuesta
            if response.status_code == 200:
                try:
                    respuesta_json = response.json()
                    exito = respuesta_json.get('estado') == 'OK'
                    
                    if exito:
                        print(f"   ✅ [REAL] {respuesta_json.get('mensaje', 'Enviado')}")
                    else:
                        print(f"   ❌ [REAL] {respuesta_json.get('mensaje', 'Error')}")
                    
                    return exito, respuesta_json
                
                except json.JSONDecodeError:
                    # Respuesta no es JSON
                    return False, {
                        "estado": "ERROR",
                        "mensaje": "Respuesta no válida de APIFAS",
                        "status_code": response.status_code,
                        "content": response.text[:200]
                    }
            else:
                return False, {
                    "estado": "ERROR",
                    "mensaje": f"HTTP {response.status_code}",
                    "status_code": response.status_code
                }
        
        except requests.Timeout:
            return False, {
                "estado": "ERROR",
                "mensaje": "Timeout al conectar con APIFAS"
            }
        
        except requests.ConnectionError:
            return False, {
                "estado": "ERROR",
                "mensaje": "No se pudo conectar con APIFAS"
            }
        
        except Exception as e:
            return False, {
                "estado": "ERROR",
                "mensaje": f"Error inesperado: {str(e)}"
            }


class CDRProcessor:
    """
    Procesa respuestas CDR de SUNAT.
    """
    
    @staticmethod
    def procesar(respuesta: Dict, cpe: Dict) -> Dict:
        """
        Procesa respuesta CDR y retorna información estructurada.
        
        Args:
            respuesta: Dict de respuesta de APIFAS
            cpe: Comprobante original normalizado
        
        Returns:
            Dict con información procesada del CDR
        """
        resultado = {
            'comprobante': f"{cpe['serie']}-{cpe['numero']:08d}",
            'fecha_proceso': respuesta.get('fecha_proceso', datetime.now().isoformat()),
            'estado_apifas': respuesta.get('estado', 'DESCONOCIDO'),
            'mensaje_apifas': respuesta.get('mensaje', ''),
            'hash_cpe': respuesta.get('hash_cpe', ''),
        }
        
        # Procesar CDR de SUNAT si existe
        if 'cdr' in respuesta:
            cdr = respuesta['cdr']
            resultado['codigo_sunat'] = cdr.get('codigo_sunat', '')
            resultado['descripcion_sunat'] = cdr.get('descripcion_sunat', '')
            resultado['notas_sunat'] = cdr.get('notas', [])
            
            # Determinar si fue aceptado por SUNAT
            codigo = str(cdr.get('codigo_sunat', ''))
            resultado['aceptado_sunat'] = codigo == '0'
        else:
            resultado['codigo_sunat'] = ''
            resultado['descripcion_sunat'] = ''
            resultado['notas_sunat'] = []
            resultado['aceptado_sunat'] = False
        
        return resultado
    
    @staticmethod
    def guardar_cdr(cdr_info: Dict, output_dir: str = "output/cdr"):
        """
        Guarda información del CDR en archivo JSON.
        
        Args:
            cdr_info: Dict con información del CDR procesado
            output_dir: Directorio donde guardar
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{cdr_info['comprobante']}_CDR.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cdr_info, f, indent=2, ensure_ascii=False)
        
        return str(filepath)


# ========================================
# CLI
# ========================================

def main():
    """CLI para enviar TXT a APIFAS"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Envío de TXT a APIFAS (mock o real)"
    )
    parser.add_argument('txt_file', help='Archivo TXT a enviar')
    parser.add_argument('--mode', choices=['mock', 'real'], default='mock',
                        help='Modo de envío (default: mock)')
    parser.add_argument('--url', help='URL APIFAS (modo real)')
    parser.add_argument('--usuario', help='Usuario APIFAS (modo real)')
    parser.add_argument('--token', help='Token APIFAS (modo real)')
    
    args = parser.parse_args()
    
    try:
        # Crear sender
        sender = APISender(
            mode=args.mode,
            url=args.url,
            usuario=args.usuario,
            token=args.token
        )
        
        # Enviar
        print(f"\n📤 Enviando comprobante...\n")
        exito, respuesta = sender.enviar(args.txt_file)
        
        # Mostrar resultado
        print(f"\n{'='*60}")
        if exito:
            print("✅ ENVÍO EXITOSO")
        else:
            print("❌ ENVÍO FALLIDO")
        print(f"{'='*60}\n")
        
        print(json.dumps(respuesta, indent=2, ensure_ascii=False))
        print()
        
        return 0 if exito else 1
    
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
