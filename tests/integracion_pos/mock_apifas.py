"""
mock_apifas.py
==============
Servidor mock de APIFAS — Motor CPE v3.0

Simula las respuestas de APIFAS localmente para testing.
Permite probar el flujo completo SIN necesidad de envío real.

Funcionalidades:
- Simula endpoint de producción SUNAT
- Simula endpoint de producción OSE
- Genera CDR fake pero realista
- Registra todos los TXT recibidos
- Configurable: éxito/error, tiempos de respuesta

Uso:
    # Iniciar servidor en puerto 8080
    python mock_apifas.py
    
    # Configurar Motor CPE para usar mock
    # En src/sender.py cambiar:
    # URL_APIFAS = "http://localhost:8080/produccion_text.php"

Autor: Fernando Miguel Tejada Quevedo (@fhertejadaDEV)
Empresa: DisateQ™
Fecha: Abril 2026
"""

import json
import time
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import hashlib


class ConfiguracionMock:
    """Configuración del servidor mock."""
    
    # Puerto del servidor
    PUERTO = 8080
    
    # Carpeta para logs
    CARPETA_LOGS = Path("./mock_apifas_logs")
    
    # Simular errores (porcentaje 0-100)
    TASA_ERROR = 0  # 0 = siempre exitoso, 100 = siempre error
    
    # Delay en segundos (simular latencia de red)
    DELAY_RESPUESTA = 0.5
    
    # Tipos de respuesta
    MODO_RESPUESTA = "exitoso"  # "exitoso", "rechazado", "observado", "timeout"
    
    # Códigos de respuesta SUNAT
    CODIGOS_SUNAT = {
        "exitoso": "0",
        "rechazado": "2001",
        "observado": "2324",
        "timeout": "9999"
    }
    
    MENSAJES_SUNAT = {
        "exitoso": "La Factura numero F001-1234, ha sido aceptada",
        "rechazado": "El numero de RUC del emisor no esta activo",
        "observado": "La serie no corresponde al tipo de comprobante",
        "timeout": "Timeout al conectar con SUNAT"
    }


class ApifasMockHandler(BaseHTTPRequestHandler):
    """Handler para peticiones HTTP del mock."""
    
    def log_message(self, format, *args):
        """Sobreescribir para customizar logs."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {format % args}")
    
    def _configurar_headers_respuesta(self):
        """Configura headers de respuesta HTTP."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
    
    def _generar_hash_cdr(self, serie: str, numero: str) -> str:
        """
        Genera hash único para el CDR.
        
        Args:
            serie: Serie del comprobante
            numero: Número del comprobante
        
        Returns:
            Hash MD5 de 32 caracteres
        """
        timestamp = str(int(time.time()))
        datos = f"{serie}-{numero}-{timestamp}"
        return hashlib.md5(datos.encode()).hexdigest()
    
    def _extraer_datos_txt(self, contenido_txt: str) -> dict:
        """
        Extrae datos básicos del TXT para generar respuesta.
        
        Args:
            contenido_txt: Contenido del archivo TXT
        
        Returns:
            Dict con datos extraídos (serie, numero, tipo, etc.)
        """
        lineas = contenido_txt.strip().split('\n')
        
        # Parsear línea 1 (cabecera)
        if len(lineas) < 1:
            return {}
        
        datos_cabecera = {}
        partes = lineas[0].split('|')
        for i in range(0, len(partes) - 1, 2):
            key = partes[i].strip()
            value = partes[i + 1].strip() if i + 1 < len(partes) else ""
            datos_cabecera[key] = value
        
        return {
            'tipo': datos_cabecera.get('TIPO', '01'),
            'serie': datos_cabecera.get('SERIE', 'F001'),
            'numero': datos_cabecera.get('NUMERO', '0000'),
            'fecha': datos_cabecera.get('FECHA', datetime.now().strftime('%Y-%m-%d'))
        }
    
    def _generar_nombre_xml_cdr(self, ruc: str, tipo: str, serie: str, numero: str) -> str:
        """
        Genera nombre del archivo XML CDR según estándar SUNAT.
        
        Args:
            ruc: RUC del emisor
            tipo: Tipo de documento (01, 03, etc.)
            serie: Serie del comprobante
            numero: Número del comprobante
        
        Returns:
            Nombre del archivo CDR
        """
        numero_formateado = str(numero).zfill(8)
        return f"R-{ruc}-{tipo}-{serie}-{numero_formateado}.xml"
    
    def _generar_respuesta_exitosa(self, datos: dict) -> dict:
        """
        Genera respuesta exitosa simulada.
        
        Args:
            datos: Datos extraídos del TXT
        
        Returns:
            Dict con respuesta en formato APIFAS
        """
        serie = datos.get('serie', 'F001')
        numero = datos.get('numero', '0000')
        tipo = datos.get('tipo', '01')
        
        # RUC fijo de prueba (DisateQ)
        ruc_emisor = "20123456789"
        
        hash_cdr = self._generar_hash_cdr(serie, numero)
        nombre_xml = self._generar_nombre_xml_cdr(ruc_emisor, tipo, serie, numero)
        
        return {
            "success": True,
            "codigo_sunat": ConfiguracionMock.CODIGOS_SUNAT["exitoso"],
            "mensaje_sunat": f"La Factura numero {serie}-{numero}, ha sido aceptada",
            "hash_cdr": hash_cdr,
            "nombre_xml_cdr": nombre_xml,
            "fecha_respuesta": datetime.now().isoformat(),
            "ticket": f"TICKET-{int(time.time())}-{hash_cdr[:8]}",
            "observaciones": [],
            "es_mock": True  # Indicador de que es respuesta fake
        }
    
    def _generar_respuesta_rechazada(self, datos: dict) -> dict:
        """Genera respuesta de rechazo simulada."""
        serie = datos.get('serie', 'F001')
        numero = datos.get('numero', '0000')
        
        return {
            "success": False,
            "codigo_sunat": ConfiguracionMock.CODIGOS_SUNAT["rechazado"],
            "mensaje_sunat": ConfiguracionMock.MENSAJES_SUNAT["rechazado"],
            "hash_cdr": None,
            "nombre_xml_cdr": None,
            "fecha_respuesta": datetime.now().isoformat(),
            "ticket": None,
            "observaciones": [
                "El RUC del emisor no existe en el padrón de SUNAT"
            ],
            "es_mock": True
        }
    
    def _generar_respuesta_observada(self, datos: dict) -> dict:
        """Genera respuesta con observaciones simulada."""
        serie = datos.get('serie', 'F001')
        numero = datos.get('numero', '0000')
        tipo = datos.get('tipo', '01')
        
        ruc_emisor = "20123456789"
        hash_cdr = self._generar_hash_cdr(serie, numero)
        nombre_xml = self._generar_nombre_xml_cdr(ruc_emisor, tipo, serie, numero)
        
        return {
            "success": True,
            "codigo_sunat": ConfiguracionMock.CODIGOS_SUNAT["observado"],
            "mensaje_sunat": f"La Factura numero {serie}-{numero}, ha sido aceptada con observaciones",
            "hash_cdr": hash_cdr,
            "nombre_xml_cdr": nombre_xml,
            "fecha_respuesta": datetime.now().isoformat(),
            "ticket": f"TICKET-{int(time.time())}-{hash_cdr[:8]}",
            "observaciones": [
                "La dirección del cliente no es válida",
                "El código de producto no está en el catálogo"
            ],
            "es_mock": True
        }
    
    def _guardar_log_peticion(self, txt_contenido: str, respuesta: dict):
        """
        Guarda log de la petición recibida.
        
        Args:
            txt_contenido: Contenido del TXT recibido
            respuesta: Respuesta generada
        """
        # Crear carpeta de logs si no existe
        ConfiguracionMock.CARPETA_LOGS.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Guardar TXT recibido
        archivo_txt = ConfiguracionMock.CARPETA_LOGS / f"{timestamp}_recibido.txt"
        archivo_txt.write_text(txt_contenido, encoding='utf-8')
        
        # Guardar respuesta generada
        archivo_json = ConfiguracionMock.CARPETA_LOGS / f"{timestamp}_respuesta.json"
        archivo_json.write_text(
            json.dumps(respuesta, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
    
    def do_POST(self):
        """Maneja peticiones POST."""
        # Parsear ruta
        ruta = self.path
        
        # Solo aceptar rutas de APIFAS
        if ruta not in ['/produccion_text.php', '/ose_produccion.php']:
            self.send_error(404, "Endpoint no encontrado")
            return
        
        # Leer contenido de la petición
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        # Parsear datos POST
        params = parse_qs(body)
        
        # Extraer TXT (puede venir como 'txt' o 'data')
        txt_contenido = ""
        if 'txt' in params:
            txt_contenido = params['txt'][0]
        elif 'data' in params:
            txt_contenido = params['data'][0]
        
        if not txt_contenido:
            self.send_error(400, "No se recibió contenido TXT")
            return
        
        # Simular delay de red
        time.sleep(ConfiguracionMock.DELAY_RESPUESTA)
        
        # Extraer datos del TXT
        datos = self._extraer_datos_txt(txt_contenido)
        
        # Generar respuesta según configuración
        modo = ConfiguracionMock.MODO_RESPUESTA
        
        if modo == "exitoso":
            respuesta = self._generar_respuesta_exitosa(datos)
        elif modo == "rechazado":
            respuesta = self._generar_respuesta_rechazada(datos)
        elif modo == "observado":
            respuesta = self._generar_respuesta_observada(datos)
        else:  # timeout
            time.sleep(30)  # Simular timeout
            respuesta = {
                "success": False,
                "codigo_sunat": ConfiguracionMock.CODIGOS_SUNAT["timeout"],
                "mensaje_sunat": ConfiguracionMock.MENSAJES_SUNAT["timeout"],
                "es_mock": True
            }
        
        # Guardar log
        self._guardar_log_peticion(txt_contenido, respuesta)
        
        # Enviar respuesta
        self._configurar_headers_respuesta()
        self.wfile.write(json.dumps(respuesta, ensure_ascii=False).encode('utf-8'))
        
        # Log en consola
        estado = "✅ ÉXITO" if respuesta.get('success') else "❌ ERROR"
        print(f"{estado} | {datos.get('serie', '???')}-{datos.get('numero', '???')} | Código: {respuesta.get('codigo_sunat', 'N/A')}")
    
    def do_GET(self):
        """Maneja peticiones GET (página de estado)."""
        if self.path == '/':
            self._configurar_headers_respuesta()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Mock APIFAS - DisateQ™</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; }}
                    h1 {{ color: #2c3e50; }}
                    .status {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
                    .activo {{ background: #d4edda; color: #155724; }}
                    .info {{ background: #d1ecf1; color: #0c5460; }}
                    pre {{ background: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }}
                    .config {{ margin: 20px 0; }}
                    .config label {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔧 Mock APIFAS — Motor CPE v3.0</h1>
                    
                    <div class="status activo">
                        ✅ Servidor mock activo en puerto {ConfiguracionMock.PUERTO}
                    </div>
                    
                    <div class="status info">
                        🎯 Modo: {ConfiguracionMock.MODO_RESPUESTA.upper()}
                    </div>
                    
                    <h2>Configuración Actual</h2>
                    <div class="config">
                        <p><label>Puerto:</label> {ConfiguracionMock.PUERTO}</p>
                        <p><label>Modo respuesta:</label> {ConfiguracionMock.MODO_RESPUESTA}</p>
                        <p><label>Delay:</label> {ConfiguracionMock.DELAY_RESPUESTA}s</p>
                        <p><label>Tasa error:</label> {ConfiguracionMock.TASA_ERROR}%</p>
                        <p><label>Carpeta logs:</label> {ConfiguracionMock.CARPETA_LOGS}</p>
                    </div>
                    
                    <h2>Endpoints Disponibles</h2>
                    <pre>POST http://localhost:{ConfiguracionMock.PUERTO}/produccion_text.php
POST http://localhost:{ConfiguracionMock.PUERTO}/ose_produccion.php</pre>
                    
                    <h2>Uso con Motor CPE</h2>
                    <pre>
# En src/sender.py, cambiar:
URL_APIFAS = "http://localhost:{ConfiguracionMock.PUERTO}/produccion_text.php"

# O configurar en YAML:
envio:
  modo: legacy
  legacy:
    url: "http://localhost:{ConfiguracionMock.PUERTO}/produccion_text.php"
                    </pre>
                    
                    <h2>Cambiar Configuración</h2>
                    <pre>
# Editar mock_apifas.py, clase ConfiguracionMock:

MODO_RESPUESTA = "exitoso"    # exitoso, rechazado, observado, timeout
DELAY_RESPUESTA = 0.5         # Segundos
TASA_ERROR = 0                # 0-100%
PUERTO = 8080                 # Puerto del servidor
                    </pre>
                    
                    <p style="text-align: center; color: #7f8c8d; margin-top: 40px;">
                        DisateQ™ — Motor CPE v3.0
                    </p>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_error(404, "Página no encontrada")


def main():
    """Inicia el servidor mock."""
    print("=" * 70)
    print("MOCK APIFAS — Motor CPE DisateQ™ v3.0")
    print("=" * 70)
    print(f"Puerto: {ConfiguracionMock.PUERTO}")
    print(f"Modo: {ConfiguracionMock.MODO_RESPUESTA}")
    print(f"Delay: {ConfiguracionMock.DELAY_RESPUESTA}s")
    print(f"Logs: {ConfiguracionMock.CARPETA_LOGS}")
    print("")
    print("Endpoints:")
    print(f"  - http://localhost:{ConfiguracionMock.PUERTO}/produccion_text.php")
    print(f"  - http://localhost:{ConfiguracionMock.PUERTO}/ose_produccion.php")
    print("")
    print("Página estado:")
    print(f"  - http://localhost:{ConfiguracionMock.PUERTO}/")
    print("")
    print("Presiona Ctrl+C para detener el servidor")
    print("=" * 70)
    print("")
    
    # Crear carpeta de logs
    ConfiguracionMock.CARPETA_LOGS.mkdir(exist_ok=True)
    
    # Iniciar servidor
    server = HTTPServer(('localhost', ConfiguracionMock.PUERTO), ApifasMockHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("")
        print("=" * 70)
        print("🛑 Servidor detenido por el usuario")
        print("=" * 70)
        server.shutdown()


if __name__ == "__main__":
    main()
