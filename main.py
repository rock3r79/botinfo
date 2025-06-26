import os
import re
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get('BOT_TOKEN')  # Usa variable de entorno
app = Flask(__name__)

# Inicializar bot
bot = Bot(token=TOKEN)
application = Application.builder().token(TOKEN).build()

# Funci¨®n para parsear la url m3u (simple ejemplo)
def parse_player_api(base_url, username, password):
    api_url = f"{base_url}/player_api.php?username={username}&password={password}"
    try:
        resp = requests.get(api_url, timeout=10).json()
        return resp
    except Exception as e:
        return {"error": str(e)}

# Handler /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Env¨ªame /m3u <url> para analizar una URL m3u.")

# Handler /m3u
async def m3u_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Uso: /m3u <url_m3u>')
        return

    m3u_url = context.args[0]
    match = re.match(r"(https?://[^/]+)/get\.php\?username=([^&]+)&password=([^&]+)", m3u_url)
    if not match:
        await update.message.reply_text('Enlace inv¨¢lido')
        return

    base_url, username, password = match.groups()
    data = parse_player_api(base_url, username, password)

    if "error" in data:
        await update.message.reply_text(f"Error al consultar API: {data['error']}")
        return

    estado = data.get('user_info', {}).get('status', 'Desconocido')
    conexiones = f"{data.get('user_info', {}).get('active_cons', '?')}/{data.get('user_info', {}).get('max_connections', '?')}"
    expiracion = data.get('user_info', {}).get('exp_date', 'Desconocida')

    reply = (
        f"Panel: {base_url}\n"
        f"Estado: {estado}\n"
        f"Conexiones: {conexiones}\n"
        f"Expiraci¨®n: {expiracion}"
    )
    await update.message.reply_text(reply)

# A?adir handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("m3u", m3u_command))

# Endpoint webhook para recibir actualizaciones
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return 'ok', 200

if __name__ == '__main__':
    # En local para probar
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
