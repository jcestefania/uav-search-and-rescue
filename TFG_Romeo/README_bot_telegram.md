# Guía de Configuración: Bot de Telegram

Esta guía te ayudará a crear y configurar un bot de Telegram para recibir notificaciones automáticas de tus simulaciones.

## Tabla de Contenidos

1. ¿Qué es BotFather?
2. Crear tu bot con BotFather
3. Obtener tu CHAT_ID
4. Configurar el bot en tu código
5. Probar la configuración
6. Solución de problemas
7. Seguridad y buenas prácticas

## 1. ¿Qué es BotFather?

BotFather es el bot oficial de Telegram que te permite crear y gestionar otros bots. Es como el "bot de bots" - tu punto de entrada para crear automatizaciones en Telegram.

Usuario de Telegram: @BotFather

## 2. Crear tu bot con BotFather

### Paso 1: Iniciar conversación con BotFather

- Abre Telegram en tu móvil o computadora
- Busca @BotFather en la barra de búsqueda
- Haz clic en el bot oficial (tiene la verificación azul)
- Presiona el botón START o envía /start

### Paso 2: Crear el bot

Envía el comando:

```
/newbot
```

BotFather te pedirá un nombre para tu bot. Este es el nombre visible:

```
Ejemplo: Simulador Notificaciones
```

Luego te pedirá un username (debe terminar en 'bot'):

```
Ejemplo: simulador_notif_bot
```

**Importante:** El username debe ser único y terminar en bot

### Paso 3: Guardar el TOKEN

Una vez creado, BotFather te enviará un mensaje similar a:

```
Done! Congratulations on your new bot. You will find it at t.me/simulador_notif_bot

Use this token to access the HTTP API:
8340887367:AAG-uOUAQ2oVMrfhjM4wLeXA8hHxCGIt26E

For a description of the Bot API, see this page: https://core.telegram.org/bots/api
```

Guarda el TOKEN (la línea de números y letras). Lo necesitarás más adelante.

Formato del TOKEN: `XXXXXXXXXX:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

## 3. Obtener tu CHAT_ID

El CHAT_ID es tu identificador personal en Telegram. Necesitas este número para que el bot sepa a quién enviar mensajes.

### Método 1: Usando @userinfobot (Más fácil)

- Busca @userinfobot en Telegram
- Presiona START
- El bot te responderá con tu información, incluyendo tu CHAT_ID
- Copia el número que aparece como Id (será un número largo)

Ejemplo de respuesta:

```
Id: 2114172581
First name: Romeo
...
```

### Método 2: Usando @RawDataBot (Alternativa)

- Busca @RawDataBot en Telegram
- Presiona START
- El bot te enviará un JSON con tu información
- Busca el campo "id" dentro de "from"

```json
{
  "update_id": ...,
  "message": {
    "from": {
      "id": 2114172581,
      ...
    }
  }
}
```

### Método 3: Manual (Para desarrolladores)

- Inicia una conversación con tu bot (búscalo por su username)
- Envíale cualquier mensaje (por ejemplo: "Hola")
- Abre en tu navegador:

```
https://api.telegram.org/bot<TU_TOKEN>/getUpdates
```

Reemplaza `<TU_TOKEN>` con tu token real

- Busca en el JSON el campo `"chat":{"id": XXXXXXX}`

## 4. Configurar el bot en tu código

### Opción A: Directamente en el código (No recomendado para producción)

```python
# En tu notebook o script
TELEGRAM_TOKEN = "8340887367:AAG-uOUAQ2oVMrfhjM4wLeXA8hHxCGIt26E"
CHAT_ID = "2114172581"
```

**Cuidado:** No compartas este código públicamente si tiene tus credenciales reales.

### Opción B: Usando variables de entorno (Recomendado)

**En Windows:**

Crea un archivo .env en la raíz de tu proyecto:

```env
TELEGRAM_TOKEN=8340887367:AAG-uOUAQ2oVMrfhjM4wLeXA8hHxCGIt26E
TELEGRAM_CHAT_ID=2114172581
```

Instala python-dotenv:

```bash
pip install python-dotenv
```

En tu código:

```python
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
```

**En Linux/Mac:**

Exporta las variables en tu terminal:

```bash
export TELEGRAM_TOKEN="tu_token_aquí"
export TELEGRAM_CHAT_ID="tu_chat_id_aquí"
```

O añádelas a tu .bashrc o .zshrc para hacerlas permanentes.

## 5. Probar la configuración

### Script de prueba rápido

Crea un archivo test_telegram.py:

```python
import requests

TELEGRAM_TOKEN = "TU_TOKEN_AQUÍ"
CHAT_ID = "TU_CHAT_ID_AQUÍ"

def enviar_mensaje_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": mensaje}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Mensaje enviado correctamente!")
            print(f"Respuesta: {response.json()}")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

# Prueba
enviar_mensaje_telegram("¡Bot configurado correctamente!")
```

Ejecuta:

```bash
python test_telegram.py
```

Si todo está bien, recibirás un mensaje en Telegram.

## 6. Solución de problemas

### Error: "Unauthorized" o "401"

**Causa:** Token incorrecto o mal formateado

**Solución:**

- Verifica que copiaste el token completo
- Asegúrate de no tener espacios al inicio o final
- Regenera el token con BotFather usando /token

### Error: "Bad Request: chat not found" o "400"

**Causa:** CHAT_ID incorrecto o el bot no ha iniciado conversación contigo

**Solución:**

- Busca tu bot en Telegram por su username
- Presiona START o envíale un mensaje
- Verifica tu CHAT_ID con @userinfobot
- Asegúrate de que el CHAT_ID sea un número (sin comillas en el código)

### No recibo mensajes

**Causa:** El bot no puede iniciar conversaciones, debes hablarle primero

**Solución:**

- Abre Telegram
- Busca tu bot por su username
- Presiona START
- Envíale cualquier mensaje
- Ahora intenta ejecutar tu script de nuevo

### Error: "requests.exceptions.ConnectionError"

**Causa:** Sin conexión a internet o firewall bloqueando

**Solución:**

- Verifica tu conexión a internet
- Comprueba que no haya un firewall bloqueando Python
- Intenta acceder a https://api.telegram.org desde tu navegador

## 7. Seguridad y buenas prácticas

### Protege tu TOKEN

- NUNCA subas tu token a repositorios públicos (GitHub, GitLab, etc.)
- Añade .env a tu .gitignore:

```
# .gitignore
.env
*.env
```

- Si accidentalmente expones tu token:
  - Usa BotFather para regenerarlo: /revoke
  - Luego crea uno nuevo: /token

### Limita los permisos del bot

Por defecto, tu bot solo puede:

- Enviar mensajes a quien le haya enviado un mensaje primero
- No puede leer mensajes de grupos (a menos que lo configures)

### Mensajes informativos

Estructura tus notificaciones claramente:

```python
mensaje = f"""
Simulación completada

Algoritmo: {algoritmo}
Agentes: {n_agents}
Indicios: {n_indicios}
Tiempo: {tiempo}s
"""
```

### Manejo de errores

Siempre usa try-except:

```python
try:
    enviar_mensaje_telegram(mensaje)
except Exception as e:
    print(f"No se pudo enviar notificación: {e}")
    # Tu código continúa ejecutándose
```

### Rate limiting

Telegram limita a ~30 mensajes por segundo

## Checklist final

Antes de ejecutar tus simulaciones, verifica:

- [ ] Bot creado con BotFather
- [ ] TOKEN guardado de forma segura
- [ ] CHAT_ID obtenido
- [ ] Conversación iniciada con el bot (presionaste START)
- [ ] Script de prueba ejecutado correctamente
- [ ] Variables configuradas en tu código
- [ ] .env añadido a .gitignore (si usas Git)
