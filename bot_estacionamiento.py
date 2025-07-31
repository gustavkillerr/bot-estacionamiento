from telegram import Update, ReplyKeyboardMarkup 
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import pytz
import os
import requests
from bs4 import BeautifulSoup
from keep_alive import keep_alive  # 👈 Importar servidor Flask

# Zona horaria Argentina
ARG_TIMEZONE = pytz.timezone("America/Argentina/Buenos_Aires")
PRECIO_POR_HORA = 1000
ENTRADA_PATENTE, SALIDA_PATENTE = range(2)
autos_en_estacionamiento = {}

main_keyboard = ReplyKeyboardMarkup([["Entrada", "Salida"]], resize_keyboard=True)

def obtener_dolar_blue():
    try:
        response = requests.get("https://dolarhoy.com", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        blue_div = soup.find("a", href="/cotizaciondolarblue").find_next("div", class_="val")
        valor = blue_div.text.strip().replace("$", "").replace(",", ".")
        return float(valor)
    except Exception as e:
        print(f"Error al obtener el dólar blue: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚗 Bienvenido al sistema de estacionamiento.\nElegí una opción:",
        reply_markup=main_keyboard
    )

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🅿️ Ingresá la patente del auto que está entrando:")
    return ENTRADA_PATENTE

async def guardar_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    patente = update.message.text.strip().upper()
    hora_entrada = datetime.now(ARG_TIMEZONE)
    autos_en_estacionamiento[patente] = hora_entrada
    await update.message.reply_text(
        f"✅ Entrada registrada para {patente} a las {hora_entrada.strftime('%H:%M:%S')}"
    )
    return ConversationHandler.END

async def salida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚗 Ingresá la patente del auto que está saliendo:")
    return SALIDA_PATENTE

async def procesar_salida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    patente = update.message.text.strip().upper()
    hora_salida = datetime.now(ARG_TIMEZONE)

    if patente not in autos_en_estacionamiento:
        await update.message.reply_text("⚠️ No se encontró una entrada registrada para esa patente.")
        return ConversationHandler.END

    hora_entrada = autos_en_estacionamiento.pop(patente)
    duracion = hora_salida - hora_entrada
    segundos = duracion.total_seconds()
    minutos = int(segundos // 60)
    segundos_restantes = int(segundos % 60)

    precio_total = round((segundos / 3600) * PRECIO_POR_HORA, 2)

    dolar_blue = obtener_dolar_blue()
    if dolar_blue:
        precio_usd = round(precio_total / dolar_blue, 2)
        dolar_info = f"💵 Equiv. en USD: ${precio_usd} (Dólar blue: ${dolar_blue})"
    else:
        dolar_info = "⚠️ No se pudo obtener el precio del dólar."

    respuesta = (
        f"🚗 Patente: {patente}\n"
        f"🕓 Entrada: {hora_entrada.strftime('%H:%M:%S')}\n"
        f"🕕 Salida: {hora_salida.strftime('%H:%M:%S')}\n"
        f"⏳ Tiempo: {minutos} min {segundos_restantes} seg\n"
        f"💰 Total a cobrar: ${precio_total}\n"
        f"{dolar_info}"
    )
    await update.message.reply_text(respuesta)
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("Falta definir la variable BOT_TOKEN en el entorno.")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()

    entrada_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Entrada$"), entrada)],
        states={ENTRADA_PATENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_entrada)]},
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    salida_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Salida$"), salida)],
        states={SALIDA_PATENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_salida)]},
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(entrada_conv)
    app.add_handler(salida_conv)

    keep_alive()  # 🔥 Levanta el servidor Flask para evitar que Render lo duerma
    app.run_polling()  # ✅ Ejecuta el bot correctamente sin asyncio.run()
