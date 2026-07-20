import asyncio
import logging
import time
import os
from telegram import BotCommand
from telegram.ext import Application, CommandHandler
from telegram.constants import ParseMode

# ================== CONFIGURAÇÕES ==================
TOKEN = "8866261539:AAGAC5yfjfMNtjEy48UMpDahhnEPd5iSNSE"
VIP_GROUP_ID = -1001962887593
ADMIN_ID = 918023038

USADOS_FILE = "espiadinha_usados.txt"

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
    logger.info("✅ Lista zerada!")

# ================== MENU ==================
async def set_commands(app):
    commands = [
        BotCommand(command="start", description="🔄 Iniciar"),
        BotCommand(command="reset_espiadinhas", description="🔄 Zerar espiadinhas (Admin)"),
    ]
    await app.bot.set_my_commands(commands)

# ================== START ==================
async def start_command(update, context):
    user = update.effective_user
    args = context.args or []

    if "espiadinha" in args:
        logger.info(f"🔄 Espiadinha solicitada por {user.first_name} (ID: {user.id})")

        if user.id in used_users:
            await update.message.reply_text("❌ Você já usou sua espiadinha única.")
            return

        try:
            # Criar link de uso único
            invite = await context.bot.create_chat_invite_link(
                chat_id=VIP_GROUP_ID,
                member_limit=1,
                expire_date=int(time.time()) + 600,  # 10 minutos de validade
                name=f"Espiadinha_{user.id}"
            )

            save_used_user(user.id)

            await update.message.reply_text(
                "✅ **Espiadinha Liberada!**\n\n"
                f"👤 {user.first_name}\n"
                f"🔗 {invite.invite_link}\n\n"
                "⏳ Este link é de **uso único** e expira em poucos minutos.\n"
                "Você tem 2 minutos dentro do grupo.",
                parse_mode=ParseMode.MARKDOWN
            )

            # Remover usuário após 2 minutos
            context.job_queue.run_once(kick_user, 120, data={"user_id": user.id})

            # Revogar o link após 3 minutos (segurança extra)
            context.job_queue.run_once(revoke_invite, 180, data={"invite_link": invite.invite_link})

        except Exception as e:
            logger.error(f"Erro: {e}")
            await update.message.reply_text("❌ Erro ao gerar link.")
    else:
        await update.message.reply_text("👋 Use o botão de espiadinha.")

async def kick_user(context):
    data = context.job.data
    try:
        await context.bot.ban_chat_member(VIP_GROUP_ID, data["user_id"], revoke_messages=False)
        await context.bot.unban_chat_member(VIP_GROUP_ID, data["user_id"])
        logger.info(f"🚪 Usuário {data['user_id']} removido")
    except Exception as e:
        logger.error(f"Erro kick: {e}")

async def revoke_invite(context):
    try:
        # Revoga o link de convite
        await context.bot.revoke_chat_invite_link(VIP_GROUP_ID, context.job.data["invite_link"])
        logger.info("🔒 Link de espiadinha revogado")
    except Exception as e:
        logger.error(f"Erro ao revogar link: {e}")

async def reset_espiadinhas_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Apenas admin.")
        return
    reset_espiadinhas()
    await update.message.reply_text("✅ Lista zerada!")

# ================== INICIALIZAÇÃO ==================
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset_espiadinhas", reset_espiadinhas_command))
    
    asyncio.get_event_loop().run_until_complete(set_commands(app))
    
    print("✅ Bot rodando com link de uso único!")
    app.run_polling(drop_pending_updates=True)
