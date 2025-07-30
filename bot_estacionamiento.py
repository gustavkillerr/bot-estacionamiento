from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import pytz
import os

ARG_TIMEZONE = pytz.timezone("America/Argentina/Buenos_Aires")
PRECIO_POR_HORA = 1000
ENTRADA_PATENTE, SALIDA_PATENTE = range(2)
autos_en_estacionamiento = {}

main_keyboard = ReplyKeyboardMarkup([["Entrada", "Salida"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenido al sistema de estacionamiento.\nElegí una opción:", reply_markup=main_keyboard)

async def entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ingresá la patente del auto que está entrando:")
    return ENTRADA_PATENTE

async def guardar_entrada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    patente = update.message.text.strip().upper()
    hora_entrada = datetime.now(ARG_TIMEZONE)
    autos_en_estacionamiento[patente] = hora_entrada
    await update.message.reply_text(f"Entrada registrada para {patente} a las {hora_entrada.strftime('%H:%M:%S')}")
    return ConversationHandler.END

async def salida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ingresá la patente del auto que está saliendo:")
    return SALIDA_PATENTE

async def procesar_salida(update: Update, context: ContextTypes.DEFAULT_TYPE):
    patente = update.message.text.strip().upper()
    hora_salida = datetime.now(ARG_TIMEZONE)

    if patente not in autos_en_estacionamiento:
        await update.message.reply_text("No se encontró una entrada registrada para esa patente.")
        return ConversationHandler.END

    hora_entrada = autos_en_estacionamiento.pop(patente)
    duracion = hora_salida - hora_entrada
    horas = max(1, int(duracion.total_seconds() // 3600))
    total = horas * PRECIO_POR_HORA

    respuesta = (
        f"🚗 Patente: {patente}\n"
        f"🕓 Entrada: {hora_entrada.strftime('%H:%M:%S')}\n"
        f"🕕 Salida: {hora_salida.strftime('%H:%M:%S')}\n"
        f"⏳ Tiempo: {horas} hora(s)\n"
        f"💰 Total a cobrar: ${total}"
    )
    await update.message.reply_text(respuesta)
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operación cancelada.")
    return ConversationHandler.END

if __name__ == "__main__":
    import asyncio

    TOKEN = os.getenv("BOT_TOKEN")
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

    print("Bot corriendo...")
    asyncio.run(app.run_polling())
