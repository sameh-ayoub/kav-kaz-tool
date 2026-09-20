import sys
import subprocess
import tkinter as tk

required = ['discord.py', 'customtkinter', 'cryptography', 'Pillow', 'requests', 'certifi', 'aiohttp']

import_map = {
    'discord.py': 'discord',
    'Pillow': 'PIL',
    'customtkinter': 'customtkinter',
    'cryptography': 'cryptography',
    'requests': 'requests',
    'certifi': 'certifi',
    'aiohttp': 'aiohttp',
}
for pkg in required:
    try:
        __import__(import_map[pkg])
    except ImportError:
        print(f" Installing {pkg}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '--quiet'])
        except subprocess.CalledProcessError:
            print(f" Failed to install {pkg}. Trying --break-system-packages...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg, '--quiet', '--break-system-packages'])
        print(f" Installed {pkg}")

import discord
from discord import app_commands
import discord.ui
import asyncio
import customtkinter as ctk
import threading
import os
from pathlib import Path
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import webbrowser
from PIL import Image, ImageTk, ImageDraw
import io
import logging
import requests
import re
import certifi
from datetime import datetime
import aiohttp
import colorsys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("coffee_storeBot")

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

NEW_IMAGE_URL = ""

NEW_DISCORD_INVITE = "https://discord.gg/f9VhuUMTJu"

TOOL_DIR = Path(__file__).resolve().parent
BG_IMAGE_PATH = TOOL_DIR / "pack.png"
LOGO_IMAGE_PATH = TOOL_DIR / "asd dev profail.png"

THEME_PRIMARY = "#18181C"
THEME_PRIMARY_HOVER = "#2E2E36"
THEME_ACCENT = "#C7C9D4"
THEME_BG = "#050507"
THEME_PANEL = "#0A0A0E"
THEME_PANEL_ALT = "#0F0F15"
THEME_TEXT = "#FFFFFF"
THEME_TEXT_DIM = "#9CA3AF"
THEME_BORDER = "#22232C"
WINDOW_ALPHA = 1.0

PASTEBIN_URL = "aHR0cHM6Ly9wYXN0ZWJpbi5jb20vcmF3L1hBSFR1VUdL"
DISCORD_INVITE = base64.b64encode(NEW_DISCORD_INVITE.encode()).decode()
LOGO_URL = NEW_IMAGE_URL
DISCORD_ICON = NEW_IMAGE_URL
TRASH_ICON = NEW_IMAGE_URL
THUMBNAIL_URL = NEW_IMAGE_URL
IMAGE_URL = base64.b64encode(NEW_IMAGE_URL.encode()).decode()
CREDIT_TEXT = base64.b64encode("Developed by KaVkAz Team | https://discord.gg/f9VhuUMTJu".encode()).decode()

LOG_FILE = Path.home() / "nullx_bot_log.json"
TOKEN_FILE = Path.home() / "nullx_bot_tokens.json"
WHITELIST_FILE = Path.home() / "nullx_whitelist.json"

bots = {}
whitelist = {}
bot_manager = None

def load_whitelist():
    global whitelist
    if not WHITELIST_FILE.exists():
        whitelist = {}
        return
    try:
        with open(WHITELIST_FILE, 'r') as f:
            whitelist = json.load(f)
        logger.info(f"Loaded whitelist with {len(whitelist)} entries")
    except Exception as e:
        logger.error(f"Failed to load whitelist: {str(e)}")
        whitelist = {}

def save_whitelist():
    try:
        with open(WHITELIST_FILE, 'w') as f:
            json.dump(whitelist, f, indent=2)
        logger.info(f"Saved whitelist with {len(whitelist)} entries")
    except Exception as e:
        logger.error(f"Failed to save whitelist: {str(e)}")

def is_whitelisted(user_id, bot_token):
    if bot_token not in whitelist:
        return False
    return str(user_id) in whitelist[bot_token]

def add_to_whitelist(user_id, bot_token):
    if bot_token not in whitelist:
        whitelist[bot_token] = []
    if str(user_id) not in whitelist[bot_token]:
        whitelist[bot_token].append(str(user_id))
        save_whitelist()
        return True
    return False

def remove_from_whitelist(user_id, bot_token):
    if bot_token in whitelist and str(user_id) in whitelist[bot_token]:
        whitelist[bot_token].remove(str(user_id))
        save_whitelist()
        return True
    return False

def decode_data(encoded):
    try:
        return base64.b64decode(encoded).decode('utf-8')
    except Exception as e:
        logger.error(f"Decode error: {str(e)}")
        return None

def generate_key():
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'nullx_salt',
        iterations=200000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(b"nullx_secret_key"))
    return Fernet(key)

def encrypt_data(data, fernet):
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data, fernet):
    return fernet.decrypt(data.encode()).decode()

def save_tokens(tokens):
    if not tokens:
        return
    fernet = generate_key()
    data = {"tokens": [encrypt_data(token, fernet) for token in tokens]}
    with open(TOKEN_FILE, 'w') as f:
        json.dump(data, f)

def load_tokens():
    if not TOKEN_FILE.exists():
        return []
    with open(TOKEN_FILE, 'r') as f:
        data = json.load(f)
    fernet = generate_key()
    try:
        return [decrypt_data(token, fernet) for token in data.get("tokens", [])]
    except:
        return []

def log_message(user_id, message):
    try:
        logs = []
        if LOG_FILE.exists():
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)

        log_entry = {
            "user_id": user_id,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        logs.append(log_entry)

        with open(LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
        logger.info(f"Logged message from user {user_id}: {message}")
    except Exception as e:
        logger.error(f"Log error: {str(e)}")


class WhitelistView(discord.ui.View):
    def __init__(self, bot_token):
        super().__init__(timeout=None)
        self.bot_token = bot_token

    @discord.ui.button(label=" إضافة ID", style=discord.ButtonStyle.success)
    async def add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddUserModal(self.bot_token)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label=" حذف ID", style=discord.ButtonStyle.danger)
    async def remove_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RemoveUserModal(self.bot_token)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label=" عرض القائمة", style=discord.ButtonStyle.blurple)
    async def show_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.bot_token not in whitelist or not whitelist[self.bot_token]:
            await interaction.response.send_message(" قائمة المستخدمين المسموح لهم فارغة!", ephemeral=True)
            return

        users_list = whitelist[self.bot_token]
        embed = discord.Embed(
            title=" قائمة المستخدمين المسموح لهم",
            description=f"عدد المستخدمين: {len(users_list)}",
            color=discord.Color.green()
        )

        for i, user_id in enumerate(users_list, 1):
            embed.add_field(name=f"#{i}", value=f"<@{user_id}>\n`{user_id}`", inline=True)
            if i % 3 == 0:
                embed.add_field(name="\u200b", value="\u200b", inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

class AddUserModal(discord.ui.Modal, title=" إضافة مستخدم"):
    def __init__(self, bot_token):
        super().__init__()
        self.bot_token = bot_token

    user_id = discord.ui.TextInput(
        label="معرف المستخدم (ID)",
        placeholder="أدخل معرف المستخدم (مثال: 123456789012345678)",
        required=True,
        style=discord.TextStyle.short,
        min_length=17,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            if add_to_whitelist(user_id, self.bot_token):
                await interaction.response.send_message(f" تم إضافة المستخدم <@{user_id}> إلى قائمة السماح!", ephemeral=True)
                logger.info(f"Added user {user_id} to whitelist for bot {self.bot_token[:10]}...")
            else:
                await interaction.response.send_message(f" المستخدم <@{user_id}> موجود بالفعل في القائمة!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message(" معرف المستخدم غير صحيح! يرجى إدخال أرقام فقط.", ephemeral=True)

class RemoveUserModal(discord.ui.Modal, title=" حذف مستخدم"):
    def __init__(self, bot_token):
        super().__init__()
        self.bot_token = bot_token

    user_id = discord.ui.TextInput(
        label="معرف المستخدم (ID)",
        placeholder="أدخل معرف المستخدم للحذف",
        required=True,
        style=discord.TextStyle.short,
        min_length=17,
        max_length=20
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = int(self.user_id.value)
            if remove_from_whitelist(user_id, self.bot_token):
                await interaction.response.send_message(f" تم حذف المستخدم <@{user_id}> من قائمة السماح!", ephemeral=True)
                logger.info(f"Removed user {user_id} from whitelist for bot {self.bot_token[:10]}...")
            else:
                await interaction.response.send_message(f" المستخدم <@{user_id}> غير موجود في القائمة!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message(" معرف المستخدم غير صحيح! يرجى إدخال أرقام فقط.", ephemeral=True)


class MessageView(discord.ui.View):
    def __init__(self, user_id, message, client, bot_token):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.message = message
        self.client = client
        self.bot_token = bot_token

    @discord.ui.button(label=" إرسال 1", style=discord.ButtonStyle.blurple)
    async def send_single(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_whitelisted(interaction.user.id, self.bot_token):
            await interaction.response.send_message(" ليس لديك صلاحية لاستخدام هذا البوت!", ephemeral=True)
            return

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(" هذا الزر مخصص لمن أصدر الأمر فقط!", ephemeral=True)
            return
        await interaction.response.send_message(self.message)
        logger.info(f"Sent single message by {interaction.user} for bot {self.client.user}")

    @discord.ui.button(label=" إرسال 5", style=discord.ButtonStyle.green)
    async def send_five(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_whitelisted(interaction.user.id, self.bot_token):
            await interaction.response.send_message(" ليس لديك صلاحية لاستخدام هذا البوت!", ephemeral=True)
            return

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(" هذا الزر مخصص لمن أصدر الأمر فقط!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        sent_count = 0
        for _ in range(5):
            try:
                await interaction.followup.send(self.message, ephemeral=False)
                sent_count += 1
                await asyncio.sleep(0.1)
            except discord.errors.HTTPException as e:
                if e.status == 429:
                    retry_after = e.retry_after if hasattr(e, 'retry_after') else 5.0
                    logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    continue
                else:
                    logger.error(f"Error sending message: {str(e)}")
                    break
            except Exception as e:
                logger.error(f"Unexpected error sending message: {str(e)}")
                break

        await interaction.followup.send(f" تم إرسال {sent_count} رسائل!", ephemeral=True)
        logger.info(f"Sent {sent_count} messages by {interaction.user} for bot {self.client.user}")

    @discord.ui.button(label=" إرسال 50", style=discord.ButtonStyle.red)
    async def send_fifty(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_whitelisted(interaction.user.id, self.bot_token):
            await interaction.response.send_message(" ليس لديك صلاحية لاستخدام هذا البوت!", ephemeral=True)
            return

        if interaction.user.id != self.user_id:
            await interaction.response.send_message(" هذا الزر مخصص لمن أصدر الأمر فقط!", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)

        total_sent = 0
        for i in range(10):
            sent_count = 0
            for _ in range(5):
                try:
                    await interaction.followup.send(self.message, ephemeral=False)
                    sent_count += 1
                    total_sent += 1
                    await asyncio.sleep(0.1)
                except discord.errors.HTTPException as e:
                    if e.status == 429:
                        retry_after = e.retry_after if hasattr(e, 'retry_after') else 5.0
                        logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.error(f"Error sending message: {str(e)}")
                        break
                except Exception as e:
                    logger.error(f"Unexpected error sending message: {str(e)}")
                    break

            if i < 9:
                await asyncio.sleep(0.2)

        await interaction.followup.send(f" تم إرسال {total_sent} رسائل!", ephemeral=True)
        logger.info(f"Sent {total_sent} messages by {interaction.user} for bot {self.client.user}")


def create_bot(token):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    client = discord.Client(intents=intents)
    command_tree = app_commands.CommandTree(client)

    @client.event
    async def on_ready():
        logger.info(f'KaVkAz Team - Bot {client.user} is working')
        await command_tree.sync()
        if bot_manager:
            bot_manager.update_status(token, f"Connected as {client.user}", "#1E90FF")
            bot_manager.log_message(token, f"Bot connected: {client.user}")

        try:
            owner_id = (await client.application_info()).owner.id
            if add_to_whitelist(owner_id, token):
                logger.info(f"Added owner {owner_id} to whitelist for bot {client.user}")
        except Exception as e:
            logger.error(f"Failed to add owner to whitelist: {str(e)}")

    @command_tree.command(name="sendmessage", description="إرسال رسالة تفاعلية باستخدام أزرار مخصصة")
    @app_commands.describe(message="الرسالة التي سيتم إرسالها عند النقر على الأزرار")
    async def send_message(interaction: discord.Interaction, message: str):
        if not is_whitelisted(interaction.user.id, token):
            await interaction.response.send_message(" ليس لديك صلاحية لاستخدام هذا البوت!", ephemeral=True)
            return

        log_message(interaction.user.id, message)

        embed = discord.Embed(
            title=" لوحة التحكم بالرسائل",
            description="استخدم الأزرار أدناه لإرسال رسالتك!",
            color=discord.Color.from_rgb(30, 144, 255),
            timestamp=discord.utils.utcnow()
        )
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        if NEW_IMAGE_URL:
            embed.set_thumbnail(url=NEW_IMAGE_URL)
        embed.add_field(name=" الرسالة", value=f"```{message}```", inline=False)
        embed.add_field(name=" انضم إلينا", value=f"[اضغط هنا]({NEW_DISCORD_INVITE})", inline=False)
        embed.set_footer(text=decode_data(CREDIT_TEXT), icon_url=client.user.avatar.url if client.user.avatar else None)
        if NEW_IMAGE_URL:
            embed.set_image(url=NEW_IMAGE_URL)

        view = MessageView(interaction.user.id, message, client, token)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        logger.info(f"Sendmessage command used by {interaction.user} for bot {client.user}")

    @command_tree.command(name="whitelist", description="إدارة قائمة المستخدمين المسموح لهم باستخدام البوت")
    async def whitelist_command(interaction: discord.Interaction):
        try:
            owner_id = (await client.application_info()).owner.id
            if interaction.user.id != owner_id:
                await interaction.response.send_message(" فقط مالك البوت يمكنه إدارة قائمة السماح!", ephemeral=True)
                return
        except:
            await interaction.response.send_message(" حدث خطأ في التحقق من الصلاحيات!", ephemeral=True)
            return

        embed = discord.Embed(
            title=" إدارة قائمة السماح",
            description="استخدم الأزرار أدناه لإدارة المستخدمين المسموح لهم باستخدام هذا البوت",
            color=discord.Color.blurple()
        )
        embed.add_field(name="ℹ معلومات", value=f"• عدد المستخدمين المسموح لهم: {len(whitelist.get(token, []))}\n• استخدم الأزرار لإضافة أو حذف المستخدمين", inline=False)

        view = WhitelistView(token)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    return client, command_tree


def adjust_color(hex_color, factor=0.8):
    hex_color = hex_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    l = max(0, l * factor)
    rgb_new = colorsys.hls_to_rgb(h, l, s)
    return '#{:02x}{:02x}{:02x}'.format(int(rgb_new[0]*255), int(rgb_new[1]*255), int(rgb_new[2]*255))

def create_rounded_image(image, size=(40, 40)):
    image = image.resize(size, Image.LANCZOS)
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    output = Image.new('RGBA', size, (0, 0, 0, 0))
    output.paste(image, (0, 0), mask)
    return output

def fetch_bot_avatar(token):
    try:
        intents = discord.Intents.default()
        client = discord.Client(intents=intents)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(client.login(token))
            avatar_url = client.user.avatar.url if client.user.avatar else None
            loop.run_until_complete(client.close())
            if avatar_url:
                response = requests.get(avatar_url, verify=certifi.where())
                if response.status_code == 200:
                    return Image.open(io.BytesIO(response.content))
            return None
        finally:
            if not loop.is_closed():
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
    except Exception as e:
        logger.warning(f"Failed to fetch bot avatar: {str(e)}")
        return None


class BotManager:
    def __init__(self, root):
        self.root = root
        self.root.title("KaVkAz Team")
        self.root.geometry("1000x720")
        self.root.resizable(False, False)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        try:
            if WINDOW_ALPHA < 1.0:
                self.root.after(120, lambda: self.root.attributes("-alpha", WINDOW_ALPHA))
        except Exception:
            pass

        load_whitelist()

        try:
            logo = Image.open(LOGO_IMAGE_PATH).resize((64, 64), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo)
            self.root.iconphoto(False, logo_photo)
            self.root_icon = logo_photo
        except Exception as e:
            logger.warning(f"Failed to load window icon: {str(e)}")

        self.canvas = tk.Canvas(self.root, width=1000, height=720,
                                highlightthickness=0, bd=0, bg="#000000")
        self.canvas.pack(fill="both", expand=True)

        try:
            bg = Image.open(BG_IMAGE_PATH).convert("RGB")
            bg = bg.resize((1000, 720), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg)
            self.canvas.create_image(0, 0, anchor="nw", image=self.bg_photo)
        except Exception as e:
            logger.warning(f"Failed to load background image: {str(e)}")

        self.canvas.create_text(45, 30, anchor="w", text="KaVkAz Team",
                                fill=THEME_TEXT, font=("Inter", 30, "bold"))

        try:
            logo = Image.open(LOGO_IMAGE_PATH).convert("RGBA")
            logo = create_rounded_image(logo, (58, 58))
            self.logo_photo = ImageTk.PhotoImage(logo)
            self.canvas.create_image(925, 38, anchor="n", image=self.logo_photo)
        except Exception as e:
            logger.warning(f"Failed to load server logo: {str(e)}")

        self.canvas.create_text(40, 115, anchor="w", text="Add New Bot Token",
                                fill=THEME_TEXT, font=("Inter", 12, "bold"))
        self.token_entry = ctk.CTkEntry(self.root, show="*", font=ctk.CTkFont("Inter", 12),
                                        width=300, height=34, corner_radius=0,
                                        fg_color="#0A0A0E", border_color="#FFFFFF",
                                        border_width=2, placeholder_text="Enter bot token",
                                        text_color=THEME_TEXT)
        self.canvas.create_window(40, 143, anchor="w", window=self.token_entry)

        self.add_token_id = self._text_button(40, 192, "+ Add Token", self.add_token, 13)
        self.start_all_id = self._text_button(40, 235, " Start All Bots", self.start_all_bots, 13)

        self.canvas.create_text(40, 295, anchor="w", text="Active Bots",
                                fill=THEME_TEXT, font=("Inter", 12, "bold"))

        self.canvas.create_text(380, 115, anchor="w", text="Activity Log",
                                fill=THEME_TEXT, font=("Inter", 12, "bold"))
        self.clear_log_id = self._text_button(770, 555, " Clear Log", self.clear_log, 12)

        self.canvas.create_text(
            500, 691, anchor="center",
            text="codeing by : comando( 23f9 )",
            fill=THEME_ACCENT, font=("Inter", 11, "bold"))

        self.log_lines = []
        self.log_items = []
        self.bot_widgets = {}
        self._avatar_refs = []

        saved_tokens = load_tokens()
        if saved_tokens:
            self.log_message("all", " Loading saved tokens...")
            for token in saved_tokens:
                self.add_token(token)
            self._rebuild_bots()

    def _text_button(self, x, y, text, command, size=13, color=THEME_TEXT,
                     hover=THEME_ACCENT, anchor="w"):
        item = self.canvas.create_text(x, y, anchor=anchor, text=text,
                                       fill=color, font=("Inter", size, "bold"))
        self.canvas.tag_bind(item, "<Button-1>", lambda e, c=command: c())
        self.canvas.tag_bind(item, "<Enter>", lambda e, i=item: self.canvas.itemconfig(i, fill=hover))
        self.canvas.tag_bind(item, "<Leave>", lambda e, i=item: self.canvas.itemconfig(i, fill=color))
        return item

    def _start_color(self, token):
        return "#FF6B6B" if bots.get(token, {}).get("running") else "#7CFF8A"

    def _rebuild_bots(self):
        for w in self.bot_widgets.values():
            for item in w.values():
                self.canvas.delete(item)
        self.bot_widgets.clear()
        self._avatar_refs = []
        y = 325
        for token in bots:
            w = {}
            avatar_photo = None
            try:
                avatar = fetch_bot_avatar(token)
                if avatar:
                    avatar = create_rounded_image(avatar, (26, 26))
                    avatar_photo = ImageTk.PhotoImage(avatar)
                    w["avatar"] = self.canvas.create_image(40, y + 13, anchor="center", image=avatar_photo)
                    self._avatar_refs.append(avatar_photo)
            except Exception as e:
                logger.warning(f"Failed to load avatar for bot: {str(e)}")
            name_x = 74 if "avatar" in w else 40
            w["name"] = self.canvas.create_text(name_x, y, anchor="nw",
                                                text=f"Token: {token[:10]}...",
                                                fill=THEME_TEXT, font=("Inter", 11, "bold"))
            w["status"] = self.canvas.create_text(225, y, anchor="nw", text="Idle",
                                                  fill=THEME_TEXT_DIM, font=("Inter", 10))
            w["indicator"] = w["status"]
            y += 18
            w["start"] = self.canvas.create_text(name_x, y, anchor="nw", text=" Start",
                                                 fill="#7CFF8A", font=("Inter", 10, "bold"))
            w["delete"] = self.canvas.create_text(name_x + 105, y, anchor="nw", text=" Remove",
                                                  fill="#FF6B6B", font=("Inter", 10))
            self.canvas.tag_bind(w["start"], "<Button-1>",
                                 lambda e, t=token: self.toggle_bot(t))
            self.canvas.tag_bind(w["start"], "<Enter>",
                                 lambda e, i=w["start"]: self.canvas.itemconfig(i, fill="#FFFFFF"))
            self.canvas.tag_bind(w["start"], "<Leave>",
                                 lambda e, i=w["start"], t=token: self.canvas.itemconfig(i, fill=self._start_color(t)))
            self.canvas.tag_bind(w["delete"], "<Button-1>",
                                 lambda e, t=token: self.remove_token(t))
            self.canvas.tag_bind(w["delete"], "<Enter>",
                                 lambda e, i=w["delete"]: self.canvas.itemconfig(i, fill="#FFFFFF"))
            self.canvas.tag_bind(w["delete"], "<Leave>",
                                 lambda e, i=w["delete"]: self.canvas.itemconfig(i, fill="#FF6B6B"))
            self.bot_widgets[token] = w
            y += 30

    def add_token(self, token=None):
        if not token:
            token = self.token_entry.get().strip()
            self.token_entry.delete(0, "end")

        if not token or len(token) < 50 or not re.match(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", token):
            self.log_message("all", " Invalid bot token format! Must be a valid Discord bot token.")
            return

        if token in bots:
            self.log_message("all", " Token already added!")
            return

        client, command_tree = create_bot(token)
        bots[token] = {
            "client": client,
            "loop": None,
            "running": False,
            "command_tree": command_tree
        }

        self._rebuild_bots()
        save_tokens(list(bots.keys()))
        self.log_message("all", f" Added token: {token[:10]}...")

    def remove_token(self, token):
        if token not in bots:
            return

        if bots[token]["running"]:
            self.stop_bot(token)

        if token in whitelist:
            del whitelist[token]
            save_whitelist()

        del bots[token]
        self._rebuild_bots()

        save_tokens(list(bots.keys()))
        self.log_message("all", f" Removed token: {token[:10]}...")

    def update_status(self, token, status, color):
        if token in self.bot_widgets:
            w = self.bot_widgets[token]
            self.canvas.itemconfig(w["status"], text=status, fill=color)
            self.canvas.itemconfig(w["indicator"], fill=color)

    def log_message(self, token, message):
        target = "All Bots" if token == "all" else f"Bot {token[:10]}..."
        line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {target}: {message}"
        self.log_lines.append(line)
        if len(self.log_lines) > 35:
            del self.log_lines[:-35]
        for item in self.log_items:
            self.canvas.delete(item)
        self.log_items = []
        y = 148
        for ln in self.log_lines:
            item = self.canvas.create_text(385, y, anchor="nw", text=ln,
                                           fill=THEME_TEXT, width=520,
                                           font=("Fira Code", 10))
            self.log_items.append(item)
            x0, y0, x1, y1 = self.canvas.bbox(item)
            y += (y1 - y0) + 4
            if y > 545:
                break

    def clear_log(self):
        self.log_lines = []
        for item in self.log_items:
            self.canvas.delete(item)
        self.log_items = []
        self.log_message("all", " Log cleared")

    def toggle_bot(self, token):
        if token not in bots:
            return

        if not bots[token]["running"]:
            self.start_bot(token)
        else:
            self.stop_bot(token)

    def start_bot(self, token):
        if token not in bots or bots[token]["running"]:
            self.log_message(token, " Bot is already running!")
            return

        if bots[token]["client"].is_closed():
            bots[token]["client"], bots[token]["command_tree"] = create_bot(token)

        bots[token]["loop"] = asyncio.new_event_loop()
        bots[token]["running"] = True
        self.canvas.itemconfig(self.bot_widgets[token]["start"], text="⏹ Stop", fill="#FF6B6B")
        self.update_status(token, "Starting...", "#FFD700")
        self.log_message(token, " Starting bot")
        threading.Thread(target=self.run_bot, args=(token,), daemon=True).start()

    def run_bot(self, token):
        asyncio.set_event_loop(bots[token]["loop"])
        try:
            logger.info(f"Attempting to start bot with token {token[:10]}...")
            bots[token]["loop"].run_until_complete(bots[token]["client"].start(token))
        except Exception as e:
            logger.error(f"Failed to start bot {token[:10]}...: {str(e)}")
            self.root.after(0, lambda: self.log_message(token, f" Failed to start bot: {str(e)}"))
            self.root.after(0, lambda: self.reset_bot(token))
        finally:
            bots[token]["running"] = False
            if bots[token]["loop"] and not bots[token]["loop"].is_closed():
                logger.info(f"Closing event loop for bot {token[:10]}...")
                bots[token]["loop"].run_until_complete(bots[token]["loop"].shutdown_asyncgens())
                bots[token]["loop"].close()
            bots[token]["loop"] = None
            self.root.after(0, lambda: self.reset_bot(token))

    def stop_bot(self, token):
        if token not in bots or not bots[token]["running"]:
            self.log_message(token, " Bot is not running!")
            return

        self.update_status(token, "Stopping...", "#FFD700")
        self.log_message(token, " Stopping bot")
        self.canvas.itemconfig(self.bot_widgets[token]["start"], text=" Start", fill="#7CFF8A")
        if bots[token]["loop"] and not bots[token]["loop"].is_closed():
            asyncio.run_coroutine_threadsafe(bots[token]["client"].close(), bots[token]["loop"])
        self.update_status(token, "Idle", "#FF4040")

    def start_all_bots(self):
        if not bots:
            self.log_message("all", " No bots added!")
            return
        for token in bots:
            if not bots[token]["running"]:
                self.start_bot(token)
        self.log_message("all", " Starting all bots...")

    def reset_bot(self, token):
        if token in self.bot_widgets:
            self.canvas.itemconfig(self.bot_widgets[token]["start"], text=" Start", fill="#7CFF8A")
            self.update_status(token, "Idle", "#FF4040")

if __name__ == "__main__":
    root = ctk.CTk()
    bot_manager = BotManager(root)
    root.mainloop()