import logging
import os
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram.constants import ParseMode

# ================== CONFIGURAÇÕES ==================
TOKEN = "8866261539:AAGAC5yfjfMNtjEy48UMpDahhnEPd5iSNSE"
DESTINO_CHANNEL = -1003598925082
VIP_GROUP_ID = -1001962887593
BOT_USERNAME = "punhetomidia1bot"
ADMIN_ID = 918023038

USADOS_FILE = "espiadinha_usados.txt"
IMAGEM_ESPIADINHA = "espiadinha.jpg"

# Logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def load_used_users():
    if os.path.exists(USADOS_FILE):
        with open(USADOS_FILE, "r") as f:
            return {int(line.strip()) for line in f if line.strip()}
    return set()

used_users = load_used_users()

def save_used_user(user_id):
    used_users.add(user_id)
    with open(USADOS_FILE, "a") as f:
        f.write(f"{user_id}\n")

def reset_espiadinhas():
    global used_users
    used_users = set()
    if os.path.exists(USADOS_FILE):
        os.remove(USADOS_FILE)
    logger.info("✅ Lista de espiadinhas zerada!")

ESPIADINHA_TEXT = """🔥 VENHA DAR UMA ESPIADINHA NO JERK BOY VIP 🔥

O maior acervo gay do Telegram está te esperando!

Aqui você vai encontrar putaria pesada, novinhos, machos, bears, twinks, packs completos, lives vazadas e muito mais.

Quer provar um gostinho agora?

👀 Aproveite sua espiadinha de 2 minutos!"""

def get_espiadinha_keyboard():
    keyboard = [[InlineKeyboardButton("👀 Entrar na Espiadinha (2 min)", url=f"https://t.me/{BOT_USERNAME}?start=espiadinha")]]
    return InlineKeyboardMarkup(keyboard)

# ================== COMANDOS ==================
async def espiadinha_command(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Apenas o administrador pode usar este comando.")
        return

    try:
        with open(IMAGEM_ESPIADINHA, "rb") as photo:
            await context.bot.send_photo(
                chat_id=DESTINO_CHANNEL,
                photo=photo,
                caption=ESPIADINHA_TEXT,
                reply_markup=get_espiadinha_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        logger.info(f"📢 Promo enviada por {user.first_name}")
        await update.message.reply_text("✅ Promo enviada no canal!")
    except FileNotFoundError:
        await update.message.reply_text("❌ Imagem 'espiadinha.jpg' não encontrada.")
    except Exception as e:
        logger.error(f"Erro promo: {e}")
        await update.message.reply_text("❌ Erro ao enviar.")

async def start_command(update, context):
    user = update.effective_user
    args = context.args

    if args and args[0] == "espiadinha":
        logger.info(f"🔄 {user.first_name} (ID:{user.id}) pediu espiadinha")

        if user.id in used_users:
            logger.info(f"🚫 {user.id} já usou")
            await update.message.reply_text("❌ Você já usou sua Espiadinha.")
            return

        try:
            expire_timestamp = int(time.time()) + 300

            invite = await context.bot.create_chat_invite_link(
                chat_id=VIP_GROUP_ID,
                member_limit=1,
                expire_date=expire_timestamp,
                name=f"Espiadinha_{user.id}"
            )

            save_used_user(user.id)

            await update.message.reply_text(
                "✅ Espiadinha Liberada!\n\n"
                f"👤 {user.first_name}\n"
                f"🔗 {invite.invite_link}\n\n"
                "⏳ 2 minutos no grupo VIP.\n"
                "Depois será removido automaticamente.\n"
                "Esta espiadinha é única!",
                parse_mode=ParseMode.MARKDOWN
            )

            logger.info(f"✅ Link gerado para {user.first_name} (ID: {user.id})")

            context.job_queue.run_once(kick_user, 120, data={"user_id": user.id, "group_id": VIP_GROUP_ID})

        except Exception as e:
            logger.error(f"Erro espiadinha {user.id}: {e}")
            await update.message.reply_text("❌ Erro ao gerar link.")
    else:
        await update.message.reply_text("Bem-vindo ao Jerk Boy VIP Bot!")

async def reset_espiadinhas_command(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Apenas o administrador pode usar este comando.")
        return

    reset_espiadinhas()
    await update.message.reply_text("✅ Lista zerada!")

async def kick_user(context):
    data = context.job.data
    try:
        await context.bot.ban_chat_member(data["group_id"], data["user_id"], revoke_messages=False)
        await context.bot.unban_chat_member(data["group_id"], data["user_id"])
        logger.info(f"🚪 Usuário {data['user_id']} removido")
    except Exception as e:
        logger.error(f"Erro kick: {e}")

async def handle_media(update, context):
    logger.info("📤 Conteúdo encaminhado")
    try:
        await context.bot.copy_message(
            chat_id=DESTINO_CHANNEL,
            from_chat_id=update.message.chat_id,
            message_id=update.message.message_id,
            caption="🔥 Novo conteúdo!",
            parse_mode=ParseMode.HTML
        )
        await update.message.reply_text("✅ Enviado!")
    except Exception as e:
        logger.error(e)

# ================== INICIALIZAÇÃO ==================
if __name__ == "__main__":
    logger.info("🤖 Bot Jerk Boy VIP iniciado!")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.VIDEO | filters.PHOTO | filters.FORWARDED, handle_media))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("espiadinha", espiadinha_command))
    app.add_handler(CommandHandler("reset_espiadinhas", reset_espiadinhas_command))
    
    print("✅ Bot rodando! Use /espiadinha")
    app.run_polling(drop_pending_updates=True)