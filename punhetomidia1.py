import asyncio
import logging
import time
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode

# ================== CONFIGURAÇÕES ==================
TOKEN = "8866261539:AAGAC5yfjfMNtjEy48UMpDahhnEPd5iSNSE"
VIP_GROUP_ID = -1001962887593
ADMIN_ID = 918023038

USADOS_FILE = "espiadinha_usados.txt"

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

# ================== MENU DE COMANDOS VISÍVEL ==================
async def set_bot_commands(app):
    commands = [
        BotCommand(command="start", description="🔄 Iniciar bot"),
        BotCommand(command="reset_espiadinhas", description="🔄 Zerar lista de espiadinhas (Admin)"),
    ]
    await app.bot.set_my_commands(commands)

# ================== COMANDOS ==================
async def start_command(update, context):
    user = update.effective_user
    args = context.args

    if args and args[0] == "espiadinha":
        logger.info(f"🔄 Usuário {user.first_name} (ID:{user.id}) pediu espiadinha")

        if user.id in used_users:
            await update.message.reply_text("❌ Você já usou sua espiadinha única.")
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
                "✅ **Espiadinha Liberada!**\n\n"
                f"👤 {user.first_name}\n"
                f"🔗 {invite.invite_link}\n\n"
                "⏳ Você tem **2 minutos** no grupo VIP.\n"
                "Após esse tempo será removido automaticamente.\n\n"
                "Aproveite com moderação!",
                parse_mode=ParseMode.MARKDOWN
            )

            context.job_queue.run_once(kick_user, 120, data={"user_id": user.id, "group_id": VIP_GROUP_ID})

        except Exception as e:
            logger.error(f"Erro espiadinha {user.id}: {e}")
            await update.message.reply_text("❌ Erro ao gerar o link.")
    else:
        await update.message.reply_text(
            "👋 Bem-vindo ao **Jerk Boy VIP Bot**!\n\n"
            "Use o botão de espiadinha para acessar temporariamente."
        )

async def kick_user(context):
    data = context.job.data
    try:
        await context.bot.ban_chat_member(data["group_id"], data["user_id"], revoke_messages=False)
        await context.bot.unban_chat_member(data["group_id"], data["user_id"])
        logger.info(f"🚪 Usuário {data['user_id']} removido do VIP")
    except Exception as e:
        logger.error(f"Erro kick: {e}")

async def reset_espiadinhas_command(update, context):
    user = update.effective_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("❌ Apenas o administrador pode usar este comando.")
        return

    reset_espiadinhas()
    await update.message.reply_text("✅ Lista de espiadinhas zerada com sucesso!")

# ================== INICIALIZAÇÃO ==================
if __name__ == "__main__":
    logger.info("🤖 Bot de Espiadinha iniciado!")
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset_espiadinhas", reset_espiadinhas_command))
    
    # Ativar menu de comandos visível
    asyncio.get_event_loop().run_until_complete(set_bot_commands(app))
    
    print("✅ Bot rodando! Comandos visíveis no menu.")
    app.run_polling(drop_pending_updates=True)
