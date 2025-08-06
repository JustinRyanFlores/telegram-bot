import os
import asyncio
import requests
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import ChatMemberHandler
from web3 import Web3
from dotenv import load_dotenv
from quotes import get_ai_quote
from db import (
    init_db,
    add_user,
    get_wallet,
    get_all_users,
    get_wish_count,
    increment_wish_count,
    get_leaderboard
)

# Load environment variables
load_dotenv()

# ENV variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_RPC = os.getenv("BASE_RPC")
JAXIM_CONTRACT = "0x082Ef77013B51f4a808e83a4d345cdc88cFdd9c4"
BOT_WALLET = os.getenv("BOT_WALLET").lower()
COVALENT_API_KEY = os.getenv("COVALENT_API_KEY")
COVALENT_BASE_URL = "https://api.covalenthq.com/v1"
CHAIN_NAME = "base-mainnet"

# Web3 connection
web3 = Web3(Web3.HTTPProvider(BASE_RPC))

app = ApplicationBuilder().token(BOT_TOKEN).build()

# JAXIM ABI (simplified)
ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    }
]

contract = web3.eth.contract(address=Web3.to_checksum_address(JAXIM_CONTRACT), abi=ABI)

# === Telegram Bot Handlers ===

async def welcome_on_added(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_status = update.my_chat_member.new_chat_member.status
    if new_status == "member":
        # Send photo with caption
        with open("jaxim.jpg", "rb") as photo:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo,
                caption=(
                    "🧞‍♂️ *Welcome!* I'm *Jaxim Jeanie*, your blockchain genie!\n\n"
                    "Use /howto to learn how to send tokens and receive magical AI quotes ✨"
                ),
                parse_mode="Markdown"
            )

app.add_handler(ChatMemberHandler(welcome_on_added, chat_member_types=["my_chat_member"]))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("assets/jaxim-welcome.gif", "rb") as gif:
            await context.bot.send_animation(
                chat_id=update.effective_chat.id,
                animation=gif,
                caption=(
                    "🗞️‍♀️ *Welcome to Jaxim Jeanie!*\n\n"
                    "I'm your friendly genie of the blockchain. To begin, register your wallet:\n"
                    "`/register <your_wallet_address>`\n\n"
                    "Send JAXIM tokens to the bot wallet to get wish credits.\n"
                    "Use `/wish` to spend a credit and receive a magical quote!\n\n"
                    "Need help? Use `/howto` for a full guide."
                ),
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        print("⚠️ Error sending animation:", e)

async def howto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "📘 *How to use Jaxim Jeanie*\n\n"
            "Here's what you can do:\n\n"
            "1️⃣ `/register <your_wallet_address>` — Register your wallet address with the bot.\n"
            "2️⃣ *Send JAXIM tokens* to this bot wallet address:\n"
            f"`{BOT_WALLET}`\n"
            "   Each token you send gives you 1 wish credit.\n"
            "3️⃣ `/balance` — Check how many wish credits you have (tokens sent minus wishes used).\n"
            "4️⃣ `/wish` — Spend a wish credit to receive a magical quote from Jeanie.\n"
            "5️⃣ `/wishcount` — See how many wishes you have made so far.\n"
            "6️⃣ `/leaderboard` — View the top wishers in the community.\n"
            "7️⃣ `/howto` — Show this help message.\n\n"
            "✨ Make sure you're on the *Base* network. Enjoy your magical journey!"
        ),
        parse_mode="Markdown"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if len(context.args) != 1:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❗ *Usage:* `/register <your_wallet_address>`",
            parse_mode="Markdown"
        )
        return

    wallet = context.args[0]
    if not web3.is_address(wallet):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❗ *Invalid wallet address.*",
            parse_mode="Markdown"
        )
        return

    current_wallet = get_wallet(user_id)
    if current_wallet:
        if current_wallet.lower() == wallet.lower():
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ *You have already registered this wallet!*\n\n`{wallet}`",
                parse_mode="Markdown"
            )
            return
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ *You are updating your wallet from:*\n`{current_wallet}`\n*to:*\n`{wallet}`",
                parse_mode="Markdown"
            )

    add_user(user_id, wallet)
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ *Wallet registered successfully!*\n\n`{wallet}`",
        parse_mode="Markdown"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    wallet = get_wallet(update.effective_user.id)
    if not wallet:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❗ *You haven't registered yet.*\nUse `/register <wallet>` first.",
            parse_mode="Markdown"
        )
        return
    try:
        tokens_sent = get_tokens_sent(wallet)
        if tokens_sent is None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ *Network error: Unable to check credits right now. Please try again later.*",
                parse_mode="Markdown"
            )
            return
        wishes_used = get_wish_count(update.effective_user.id)
        credits = max(tokens_sent - wishes_used, 0)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"💰 *Your wish credits:* `{credits}`\n",
            parse_mode="Markdown"
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ *Error checking credits:*\n`{str(e)}`",
            parse_mode="Markdown"
        )

async def wish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    wallet = get_wallet(user_id)
    if not wallet:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❗ *You haven't registered yet.*\nUse `/register <wallet>` first.",
            parse_mode="Markdown"
        )
        return
    tokens_sent = get_tokens_sent(wallet)
    if tokens_sent is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ *Network error: Unable to check credits right now. Please try again later.*",
            parse_mode="Markdown"
        )
        return
    wishes_used = get_wish_count(user_id)
    credits = tokens_sent - wishes_used
    if credits < 1:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="❗ *You don't have enough wish credits!*\nSend more JAXIM tokens to the bot wallet.",
            parse_mode="Markdown"
        )
        return
    increment_wish_count(user_id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="🧙‍♂️ *Rubbing the Lamp of Jaxim...*✨",
        parse_mode="Markdown"
    )
    quote = get_ai_quote(character="Jeanie")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"💬 *Here's your magical quote:*\n\n_{quote}_",
        parse_mode="Markdown"
    )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_leaderboard()
    if not top_users:
        await update.message.reply_text("📉 No wishes have been made yet!", parse_mode="Markdown")
        return

    text = "\U0001F3C6 *Top Wishers Leaderboard* \U0001F3C6\n\n"
    for idx, (telegram_id, wallet, count) in enumerate(top_users, 1):
        # Try to get username, fallback to telegram_id
        try:
            user = await context.bot.get_chat(telegram_id)
            username = f"@{user.username}" if user.username else user.first_name
        except Exception:
            username = f"ID:{telegram_id}"
        wallet_display = wallet if wallet else "N/A"
        text += (
            f"{idx}. {username}\n"
            f"    Wallet: `{wallet_display}`\n"
            f"    Wishes: *{count}*\n\n"
        )
    await update.message.reply_text(text, parse_mode="Markdown")

async def wishcount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = get_wish_count(update.effective_user.id)
    await update.message.reply_text(f"🧞‍♂️ *Your wish count:* `{count}`", parse_mode="Markdown")

def get_tokens_sent(wallet):
    try:
        wallet = wallet.lower()

        # Call Covalent API to get transfers of this wallet for the given token
        transfer_url = f"{COVALENT_BASE_URL}/{CHAIN_NAME}/address/{wallet}/transfers_v2/"
        transfer_params = {
            "contract-address": JAXIM_CONTRACT,
            "key": COVALENT_API_KEY
        }

        response = requests.get(transfer_url, params=transfer_params)
        if response.status_code != 200:
            print(f"⚠️ API Error: {response.status_code} - {response.text}")
            return None

        data = response.json()
        if data.get("error"):
            print(f"❌ API Error: {data.get('error_message')}")
            return None

        total_sent = 0
        for item in data["data"]["items"]:
            for transfer in item["transfers"]:
                if (
                    transfer["from_address"].lower() == wallet
                    and transfer["to_address"].lower() == BOT_WALLET
                ):
                    delta = int(transfer["delta"])
                    decimals = transfer["contract_decimals"]
                    total_sent += delta / (10 ** decimals)

        return int(total_sent)

    except Exception as e:
        print("❌ Exception:", str(e))
        return None

# === Transfer Watcher ===

async def watch_transfers(app):
    print("🔁 Watching for 1 JAXIM transfers to bot wallet...")
    last_block = web3.eth.block_number

    while True:
        try:
            latest = web3.eth.block_number
            if latest > last_block:
                events = contract.events.Transfer().get_logs(
                    from_block=last_block + 1,
                    to_block=latest
                )
                for event in events:
                    sender = event["args"]["from"]
                    receiver = event["args"]["to"]
                    amount = event["args"]["value"]

                    if receiver.lower() == BOT_WALLET.lower() and amount == web3.to_wei(1, "ether"):
                        for telegram_id, user_wallet in get_all_users():
                            if user_wallet.lower() == sender.lower():
                                print(f"💡 Detected 1 JAXIM from {sender} (Telegram ID: {telegram_id})")

                                increment_wish_count(telegram_id)

                                await app.bot.send_message(
                                    chat_id=telegram_id,
                                    text="🧙‍♂️ *Rubbing the Lamp of Jaxim...*✨",
                                    parse_mode="Markdown"
                                )

                                quote = get_ai_quote(character="Jeanie")
                                await app.bot.send_message(
                                    chat_id=telegram_id,
                                    text=f"💬 *Here's your magical quote:*\n\n_{quote}_",
                                    parse_mode="Markdown"
                                )

                last_block = latest

        except Exception as e:
            print("❌ Error watching transfers:", str(e))

        await asyncio.sleep(10)

# === Main Bot ===

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("howto", howto))
    app.add_handler(CommandHandler("register", register))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("wishcount", wishcount))  
    app.add_handler(CommandHandler("wish", wish))

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(watch_transfers(app))
    print("🤖 Bot running...")
    app.run_polling()
