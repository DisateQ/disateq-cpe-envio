"""
whatsapp_notifier.py
====================
Notificaciones de errores via WhatsApp — CPE DisateQ™

Envía alertas al técnico cuando hay errores críticos de envío.
Usa la API de CallMeBot (gratuita, sin backend propio).

Activación en 3 pasos para el técnico:
  1. Agregar +34 644 22 76 27 a contactos de WhatsApp
  2. Enviar: "I allow callmebot to send me messages"
  3. Recibirá su API KEY por WhatsApp
  Más info: https://www.callmebot.com/blog/free-api-whatsapp-messages/

Configuración en ffee_config.ini:
  [ALERTAS]
  whatsapp_activo  = SI
  whatsapp_numero  = 51999888777     (código país + número, sin + ni espacios)
  whatsapp_apikey  = 123456          (API key de CallMeBot)
  errores_umbral   = 3               (errores consecutivos para disparar alerta)

Alternativas soportadas (configurables via whatsapp_proveedor):
  callmebot   ← default, gratuito, solo para uso personal
  twilio      ← para producción, requiere cuenta de pago
"""

import logging
import urllib.parse
import urllib.request
from datetime import datetime, date
from pathlib import Path

log = logging.getLogger(__name__)

# ── Proveedores ───────────────────────────────────────────────

PROVEEDOR_CALLMEBOT = "callmebot"
PROVEEDOR_TWILIO    = "twilio"
PROVEEDOR_DEFAULT   = PROVEEDOR_CALLMEBOT

URL_CALLMEBOT = (
    "https://api.callmebot.com/whatsapp.php"
    "?phone={numero}&text={texto}&apikey={apikey}"
)

TIMEOUT_WA = 15


# ── Lógica de alertas ─────────────────────────────────────────

class WhatsAppNotifier:
    """
    Gestiona el envío de alertas WhatsApp con control de umbral.

    El umbral evita spam: solo alerta cuando los errores consecutivos
    superan el límite configurado, y luego cuando se recupera.
    """

    def __init__(self, cfg):
        self._cfg              = cfg
        self._errores_consec   = 0
        self._alerta_enviada   = False
        self._ultimo_envio:    datetime | None = None

    @property
    def activo(self) -> bool:
        return (
            self._cfg.get("ALERTAS", "whatsapp_activo", fallback="NO").upper()
            in ("SI", "SÍ", "YES", "1", "TRUE")
        )

    @property
    def numero(self) -> str:
        return self._cfg.get("ALERTAS", "whatsapp_numero", fallback="").strip()

    @property
    def apikey(self) -> str:
        return self._cfg.get("ALERTAS", "whatsapp_apikey", fallback="").strip()

    @property
    def umbral(self) -> int:
        try:
            return int(self._cfg.get("ALERTAS", "errores_umbral", fallback="3"))
        except ValueError:
            return 3

    @property
    def proveedor(self) -> str:
        return self._cfg.get(
            "ALERTAS", "whatsapp_proveedor", fallback=PROVEEDOR_DEFAULT
        ).lower()

    def registrar_exito(self):
        """Llamar tras un envío exitoso. Resetea contador y notifica recuperación."""
        if self._errores_consec >= self.umbral and self._alerta_enviada:
            # Se recuperó — notificar
            self._enviar_alerta(
                f"✅ CPE DisateQ™ — Sistema recuperado\n"
                f"Envíos funcionando normalmente.\n"
                f"Hora: {datetime.now().strftime('%H:%M:%S')}"
            )
        self._errores_consec = 0
        self._alerta_enviada  = False

    def registrar_error(self, nombre_comprobante: str, motivo: str):
        """
        Llamar tras un error de envío.
        Si se supera el umbral, envía alerta WhatsApp.
        """
        self._errores_consec += 1

        if not self.activo:
            return
        if self._errores_consec < self.umbral:
            return
        if self._alerta_enviada:
            # No repetir la misma alerta — solo una vez por racha
            return

        ruc = self._cfg.get("EMPRESA", "ruc", fallback="")
        alias = self._cfg.get("EMPRESA", "alias", fallback="").strip()
        nombre_local = alias or self._cfg.get(
            "EMPRESA", "nombre_comercial", fallback=""
        ).strip() or ruc

        mensaje = (
            f"⚠️ CPE DisateQ™ — Error de envío\n"
            f"Local: {nombre_local}\n"
            f"Comprobante: {nombre_comprobante}\n"
            f"Motivo: {motivo}\n"
            f"Errores consecutivos: {self._errores_consec}\n"
            f"Hora: {datetime.now().strftime('%H:%M:%S')}"
        )

        exito, msg_resp = self._enviar_alerta(mensaje)
        if exito:
            self._alerta_enviada = True
            log.info(f"Alerta WhatsApp enviada: {nombre_comprobante}")
        else:
            log.warning(f"No se pudo enviar alerta WhatsApp: {msg_resp}")

    def _enviar_alerta(self, mensaje: str) -> tuple[bool, str]:
        """Envía el mensaje según el proveedor configurado."""
        if not self.numero:
            return False, "Número WhatsApp no configurado"
        if not self.apikey and self.proveedor == PROVEEDOR_CALLMEBOT:
            return False, "API key WhatsApp no configurada"

        self._ultimo_envio = datetime.now()

        if self.proveedor == PROVEEDOR_CALLMEBOT:
            return _enviar_callmebot(self.numero, self.apikey, mensaje)
        elif self.proveedor == PROVEEDOR_TWILIO:
            return _enviar_twilio(self._cfg, mensaje)
        else:
            return False, f"Proveedor desconocido: {self.proveedor}"


# ── Proveedores de envío ──────────────────────────────────────

def _enviar_callmebot(numero: str, apikey: str, mensaje: str) -> tuple[bool, str]:
    """
    Envía un mensaje via CallMeBot (gratuito, uso personal).
    https://www.callmebot.com/blog/free-api-whatsapp-messages/
    """
    try:
        texto_enc = urllib.parse.quote(mensaje)
        url = URL_CALLMEBOT.format(
            numero=numero,
            texto=texto_enc,
            apikey=apikey,
        )
        req = urllib.request.Request(url, headers={"User-Agent": "CPEDisateQ/2.0"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_WA) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            if resp.status == 200:
                return True, body[:100]
            return False, f"HTTP {resp.status}: {body[:100]}"
    except Exception as e:
        return False, str(e)


def _enviar_twilio(cfg, mensaje: str) -> tuple[bool, str]:
    """
    Envía via Twilio WhatsApp API.
    Requiere: twilio_account_sid, twilio_auth_token, twilio_from, twilio_to
    en sección [ALERTAS] del config.
    """
    try:
        import base64
        account_sid = cfg.get("ALERTAS", "twilio_account_sid", fallback="")
        auth_token  = cfg.get("ALERTAS", "twilio_auth_token",  fallback="")
        from_num    = cfg.get("ALERTAS", "twilio_from",        fallback="")
        to_num      = cfg.get("ALERTAS", "twilio_to",          fallback="")

        if not all([account_sid, auth_token, from_num, to_num]):
            return False, "Credenciales Twilio incompletas"

        url  = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        data = urllib.parse.urlencode({
            "From": f"whatsapp:{from_num}",
            "To":   f"whatsapp:{to_num}",
            "Body": mensaje,
        }).encode("utf-8")

        creds = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
        req = urllib.request.Request(
            url, data=data, method="POST",
            headers={"Authorization": f"Basic {creds}",
                     "Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_WA) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return resp.status in (200, 201), body[:100]
    except Exception as e:
        return False, str(e)


# ── Helpers de configuración ──────────────────────────────────

def config_completa(cfg) -> bool:
    """Retorna True si la configuración de WhatsApp es válida."""
    activo = cfg.get("ALERTAS", "whatsapp_activo", fallback="NO").upper()
    if activo not in ("SI", "SÍ", "YES", "1", "TRUE"):
        return False
    numero = cfg.get("ALERTAS", "whatsapp_numero", fallback="").strip()
    apikey = cfg.get("ALERTAS", "whatsapp_apikey", fallback="").strip()
    return bool(numero and apikey)


def agregar_defaults_config(cfg) -> bool:
    """
    Agrega la sección [ALERTAS] con defaults al config si no existe.
    Retorna True si se agregó algo.
    """
    if not cfg.has_section("ALERTAS"):
        cfg.add_section("ALERTAS")

    defaults = {
        "whatsapp_activo":   "NO",
        "whatsapp_numero":   "",
        "whatsapp_apikey":   "",
        "whatsapp_proveedor": "callmebot",
        "errores_umbral":    "3",
    }
    agregado = False
    for clave, valor in defaults.items():
        if not cfg.has_option("ALERTAS", clave):
            cfg.set("ALERTAS", clave, valor)
            agregado = True
    return agregado


# ── Instrucciones para monitor.py ─────────────────────────────
"""
INTEGRACIÓN EN monitor.py
===========================

1. Import al inicio:
    from whatsapp_notifier import WhatsAppNotifier

2. En __init__ de Monitor:
    self._wa = WhatsAppNotifier(cfg)

3. En el bloque de ÉXITO de _procesar_comprobante:
    self._wa.registrar_exito()

4. En los bloques de ERROR de _procesar_comprobante:
    # Ejemplo para RespuestaError:
    self._wa.registrar_error(nombre, e.respuesta)

    # Ejemplo para ConexionError:
    self._wa.registrar_error(nombre, "Sin conexión a APIFAS")

5. En config.py DEFAULTS, agregar sección ALERTAS:
    "ALERTAS": {
        "whatsapp_activo":    "NO",
        "whatsapp_numero":    "",
        "whatsapp_apikey":    "",
        "whatsapp_proveedor": "callmebot",
        "errores_umbral":     "3",
    }

6. En config_wizard.py, agregar sección de alertas:
    seccion("Alertas WhatsApp")
    v_wa_activo  = campo con checkbox o combobox SI/NO
    v_wa_numero  = campo de texto (número con código país)
    v_wa_apikey  = campo de texto (API key CallMeBot)
    v_umbral     = campo numérico (1-10)

INTEGRACIÓN EN config.py
===========================
Agregar a DEFAULTS:
    "ALERTAS": {
        "whatsapp_activo":    "NO",
        "whatsapp_numero":    "",
        "whatsapp_apikey":    "",
        "whatsapp_proveedor": "callmebot",
        "errores_umbral":     "3",
    },
"""


# ── Tests ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import configparser

    print("=== Tests whatsapp_notifier ===\n")

    def make_cfg(activo="NO", numero="51999888777", apikey="123456", umbral="3"):
        cfg = configparser.ConfigParser()
        cfg.add_section("EMPRESA")
        cfg.set("EMPRESA", "ruc",    "20123456789")
        cfg.set("EMPRESA", "alias",  "Local Grau 1")
        cfg.add_section("ALERTAS")
        cfg.set("ALERTAS", "whatsapp_activo",  activo)
        cfg.set("ALERTAS", "whatsapp_numero",  numero)
        cfg.set("ALERTAS", "whatsapp_apikey",  apikey)
        cfg.set("ALERTAS", "errores_umbral",   umbral)
        return cfg

    # Test 1: inactivo no dispara
    wa = WhatsAppNotifier(make_cfg(activo="NO"))
    wa._errores_consec = 5  # forzar
    wa.registrar_error("B001-00001.txt", "Sin conexión")
    assert not wa._alerta_enviada
    print("✅  Inactivo: no dispara alerta")

    # Test 2: umbral no alcanzado
    wa2 = WhatsAppNotifier(make_cfg(activo="SI"))
    wa2.registrar_error("B001-00001.txt", "Error X")
    wa2.registrar_error("B001-00002.txt", "Error X")
    assert wa2._errores_consec == 2
    assert not wa2._alerta_enviada
    print("✅  Umbral no alcanzado: no dispara (2 < 3)")

    # Test 3: umbral alcanzado (no llamamos a _enviar_alerta real)
    wa3 = WhatsAppNotifier(make_cfg(activo="SI"))
    wa3._enviar_alerta = lambda msg: (True, "mock OK")  # mock
    wa3.registrar_error("B001-00001.txt", "Error X")
    wa3.registrar_error("B001-00002.txt", "Error X")
    wa3.registrar_error("B001-00003.txt", "Error X")
    assert wa3._errores_consec == 3
    assert wa3._alerta_enviada
    print("✅  Umbral alcanzado (3 errores): alerta disparada")

    # Test 4: no repite alerta en el mismo ciclo
    wa3.registrar_error("B001-00004.txt", "Error X")
    assert wa3._errores_consec == 4
    # _enviar_alerta solo se llama una vez (ya está _alerta_enviada=True)
    print("✅  No repite alerta en la misma racha")

    # Test 5: recuperación resetea estado
    wa3.registrar_exito()
    assert wa3._errores_consec == 0
    assert not wa3._alerta_enviada
    print("✅  registrar_exito() resetea contador y estado")

    # Test 6: config_completa
    assert not config_completa(make_cfg(activo="NO"))
    assert config_completa(make_cfg(activo="SI", numero="51999", apikey="123"))
    assert not config_completa(make_cfg(activo="SI", numero="", apikey="123"))
    print("✅  config_completa() valida correctamente")

    # Test 7: agregar_defaults_config
    cfg_vacio = configparser.ConfigParser()
    agregado = agregar_defaults_config(cfg_vacio)
    assert agregado
    assert cfg_vacio.has_section("ALERTAS")
    assert cfg_vacio.get("ALERTAS", "whatsapp_activo") == "NO"
    assert cfg_vacio.get("ALERTAS", "errores_umbral") == "3"
    # Idempotente
    agregado2 = agregar_defaults_config(cfg_vacio)
    assert not agregado2
    print("✅  agregar_defaults_config() idempotente")

    print()
    print("🎉  Todos los tests en verde.")
    print()
    print("NOTA: Para activar WhatsApp en producción:")
    print("  1. Registrar número en CallMeBot (gratuito)")
    print("  2. Configurar en ffee_config.ini sección [ALERTAS]")
    print("  3. Cambiar whatsapp_activo = SI")
