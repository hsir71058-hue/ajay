#!/usr/bin/env python3
# ==========================================
# 👑 24x7 AJAY HOSTING BOT — ROYAL PREMIUM EDITION
# ==========================================
# ✅ Force Join System
# ✅ Broadcast System
# ✅ Refer & Earn System
# ✅ Premium with FamGateway AUTO PAYMENT
# ✅ Admin Panel (Button-based)
# ✅ Video Tutorials
# ✅ Error Detection System
# ✅ Invalid File Blocker
# ✅ Server Ping Feature (Photo-style)
# ✅ AUTO MEMORY MANAGER
# ✅ AUTO KILL OLDEST FILE
# ✅ ROYAL PREMIUM DESIGN
# ==========================================

import os
import sys
import subprocess
import threading
import time
import shutil
import zipfile
import tarfile
import sqlite3
import signal
import ast
import importlib
import importlib.util
import html as html_lib
import logging
import re
import requests
import gc
from datetime import datetime

# ==========================================
# 👑 OWNER CONFIG
# ==========================================
ADMIN_ID = 8842586144
CHANNEL_ID = -1004417226136
CHANNEL_LINK = "https://t.me/+B6ehwPRcv_s2YTI9"
OWNER_USERNAME = "AJAY_MODS"
OWNER_LINK = "https://t.me/AJAY_MODS"

FAMGATEWAY_API_KEY = "FAM_E82FE18E86D7A30AEFBDD96C473A6638499BA130"
FAMGATEWAY_PAY_URL = "https://fampaygateway.site/pay.php"
FAMGATEWAY_VERIFY_URL = "https://fampaygateway.site/api/verify.php"

YOUTUBE_CHANNEL = "https://youtube.com/@linoxx444_live"

STOP_EVENT = threading.Event()

# ==========================================
# 🔧 AUTO MEMORY MANAGEMENT CONFIG
# ==========================================
RAM_AUTO_KILL_THRESHOLD = 85.0
RAM_CHECK_INTERVAL = 60
LOG_RETENTION_DAYS = 7
FILE_RETENTION_DAYS = 30
GC_INTERVAL = 3600

def install_requirements():
    requirements = ["pyTelegramBotAPI", "requests", "psutil"]
    for package in requirements:
        try:
            if package == "pyTelegramBotAPI":
                import telebot
            elif package == "psutil":
                import psutil
            elif package == "requests":
                import requests
            print(f"✅ {package} already installed")
        except ImportError:
            print(f"📦 Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} installed successfully")
            except Exception as e:
                print(f"❌ Failed to install {package}: {e}")

install_requirements()

import psutil
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger("telebot").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.WARNING)

BOT_TOKEN = "8825181183:AAGf3Z3c0S1P483UESFW57H3jbAenmTJBOM"

CPU_THRESHOLD = float(os.environ.get("CPU_THRESHOLD", "85.0"))
MEMORY_THRESHOLD = float(os.environ.get("MEMORY_THRESHOLD", "85.0"))
MAX_RUNNING_PROCESSES = int(os.environ.get("MAX_RUNNING_PROCESSES", "5"))
MAX_FILES_PER_USER = int(os.environ.get("MAX_FILES_PER_USER", "3"))
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "metadata.db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
TEMP_DIR = os.path.join(DATA_DIR, "temp")

for directory in [DATA_DIR, UPLOADS_DIR, LOGS_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

START_TIME = datetime.utcnow()

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
db_lock = threading.Lock()

def init_db():
    with db_lock:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.execute("PRAGMA cache_size=-2000")
        cur.execute('''CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT,
            filename TEXT, orig_name TEXT, path TEXT, uploaded_at TEXT,
            file_type TEXT, pid INTEGER, status TEXT DEFAULT 'Pending')''')
        cur.execute('''CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, file_id INTEGER, started_at TEXT,
            finished_at TEXT, pid INTEGER, log_path TEXT, exit_code INTEGER)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, joined_at TEXT, last_seen TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER,
            referred_id INTEGER UNIQUE, referred_username TEXT,
            referred_name TEXT, joined_at TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS premium_users (
            user_id INTEGER PRIMARY KEY, plan TEXT, activated_at TEXT, expires_at TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, user_id INTEGER, plan_key TEXT,
            amount REAL, status TEXT DEFAULT 'Pending', utr TEXT, created_at TEXT)''')
        conn.commit()

init_db()

# ==========================================
# 🗄️ DATABASE HELPERS
# ==========================================
def add_file_record(user_id, username, filename, orig_name, path, file_type, status="Pending"):
    with db_lock:
        cur = conn.cursor()
        cur.execute("INSERT INTO files (user_id, username, filename, orig_name, path, uploaded_at, file_type, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, username, filename, orig_name, path, datetime.utcnow().isoformat(), file_type, status))
        conn.commit()
        return cur.lastrowid

def list_user_files(user_id):
    cur = conn.cursor()
    cur.execute("SELECT id, filename, orig_name, uploaded_at, file_type, status, pid FROM files WHERE user_id=? ORDER BY id DESC", (user_id,))
    return cur.fetchall()

def get_file_record(file_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE id=?", (file_id,))
    return cur.fetchone()

def remove_file_record(file_id):
    with db_lock:
        cur = conn.cursor()
        cur.execute("DELETE FROM files WHERE id=?", (file_id,))
        conn.commit()

def record_run_start(file_id, pid, log_path):
    with db_lock:
        cur = conn.cursor()
        cur.execute("INSERT INTO runs (file_id, started_at, pid, log_path) VALUES (?, ?, ?, ?)",
                    (file_id, datetime.utcnow().isoformat(), pid, log_path))
        conn.commit()
        return cur.lastrowid

def record_run_finish(run_id, exit_code):
    with db_lock:
        cur = conn.cursor()
        cur.execute("UPDATE runs SET finished_at=?, exit_code=? WHERE id=?",
                    (datetime.utcnow().isoformat(), exit_code, run_id))
        conn.commit()

def update_file_status(file_id, pid, status):
    with db_lock:
        cur = conn.cursor()
        cur.execute("UPDATE files SET pid=?, status=? WHERE id=?", (pid, status, file_id))
        conn.commit()

def add_referral(referrer_id, referred_id, referred_username, referred_name):
    with db_lock:
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO referrals (referrer_id, referred_id, referred_username, referred_name, joined_at) VALUES (?, ?, ?, ?, ?)",
                        (referrer_id, referred_id, referred_username, referred_name, datetime.utcnow().isoformat()))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_referral_count(user_id):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id=?", (user_id,))
    return cur.fetchone()[0] or 0

def has_been_referred(user_id):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM referrals WHERE referred_id=?", (user_id,))
    return cur.fetchone()[0] > 0

def get_referral_bonus(user_id):
    count = get_referral_count(user_id)
    if count >= 10: return 5
    if count >= 5: return 2
    if count >= 3: return 1
    return 0

def get_effective_file_limit(user_id):
    if user_id == ADMIN_ID: return 99999
    return MAX_FILES_PER_USER + get_referral_bonus(user_id)

def get_referral_link(user_id):
    try:
        bot_info = bot.get_me()
        return f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    except:
        return f"https://t.me/YourBotUsername?start=ref_{user_id}"

# ==========================================
# 💎 PREMIUM PLANS
# ==========================================
PREMIUM_PLANS = {
    "1m": {"name": "🥉 1 Month Premium", "price": "₹49", "days": 30, "amount": 30},
    "2m": {"name": "🥈 2 Months Premium", "price": "₹86", "days": 60, "amount": 60},
    "6m": {"name": "🥇 6 Months Premium", "price": "₹135", "days": 180, "amount": 100},
}

def is_premium(user_id):
    if user_id == ADMIN_ID: return True
    cur = conn.cursor()
    cur.execute("SELECT expires_at FROM premium_users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if not row: return False
    try:
        expires = datetime.fromisoformat(row[0])
        if expires > datetime.utcnow():
            return True
        else:
            with db_lock:
                cur2 = conn.cursor()
                cur2.execute("DELETE FROM premium_users WHERE user_id=?", (user_id,))
                conn.commit()
            return False
    except:
        return False

def get_premium_expiry(user_id):
    cur = conn.cursor()
    cur.execute("SELECT expires_at FROM premium_users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def get_premium_plan_name(user_id):
    cur = conn.cursor()
    cur.execute("SELECT plan FROM premium_users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def activate_premium(user_id, plan_key):
    from datetime import timedelta
    plan = PREMIUM_PLANS.get(plan_key)
    if not plan: return False
    expires = datetime.utcnow() + timedelta(days=plan["days"])
    with db_lock:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO premium_users (user_id, plan, activated_at, expires_at) VALUES (?, ?, ?, ?)",
                    (user_id, plan["name"], datetime.utcnow().isoformat(), expires.isoformat()))
        conn.commit()
    return True

def create_payment_order(user_id, plan_key):
    try:
        plan = PREMIUM_PLANS.get(plan_key)
        if not plan: return None
        amount = plan["amount"]
        order_id = f"FG{user_id}{int(time.time())}"
        pay_url = f"{FAMGATEWAY_PAY_URL}?api_key={FAMGATEWAY_API_KEY}&amount={amount}&order_id={order_id}"
        with db_lock:
            cur = conn.cursor()
            cur.execute("INSERT OR REPLACE INTO orders (order_id, user_id, plan_key, amount, status, created_at) VALUES (?, ?, ?, ?, 'Pending', ?)",
                        (order_id, user_id, plan_key, amount, datetime.utcnow().isoformat()))
            conn.commit()
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={pay_url}"
        class Order:
            def __init__(self):
                self.order_id = order_id
                self.qr_url = qr_url
                self.upi_intent = pay_url
                self.payable_amount = amount
        return Order()
    except Exception as e:
        logger.error(f"create_payment_order error: {e}")
        return None

def verify_payment(order_id):
    try:
        url = f"{FAMGATEWAY_VERIFY_URL}?order_id={order_id}&api_key={FAMGATEWAY_API_KEY}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.error(f"Verify HTTP error: {response.status_code}")
            return None
        try:
            data = response.json()
            logger.info(f"FamGateway response: {data}")
            return data
        except Exception as e:
            logger.error(f"JSON parse error: {e}, raw: {response.text}")
            return None
    except Exception as e:
        logger.error(f"verify_payment error: {e}")
        return None

def is_payment_success(result):
    if not result: return False, None
    try:
        if result.get("status") == "success":
            data = result.get("data", {})
            return True, {"utr": data.get("utr", "N/A"), "amount": data.get("amount", 0)}
    except Exception as e:
        logger.error(f"is_payment_success error: {e}")
    return False, None

# ==========================================
# 🚀 PROCESS MANAGER
# ==========================================
processes = {}
proc_lock = threading.Lock()

def get_system_load():
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        return float(cpu), float(mem), int(len(processes))
    except Exception as e:
        logger.error(f"Error getting system load: {e}")
        return 0.0, 0.0, 0

def should_stop_due_to_load():
    load, memory, process_count = get_system_load()
    if process_count >= MAX_RUNNING_PROCESSES:
        return True, f"⚠️ Too many running processes ({process_count}/{MAX_RUNNING_PROCESSES})"
    if load >= CPU_THRESHOLD:
        return True, f"⚠️ High CPU load ({load}%)"
    if memory >= MEMORY_THRESHOLD:
        return True, f"⚠️ High memory usage ({memory}%)"
    return False, None

# ==========================================
# 📁 FILE TYPE + SECURITY HELPERS
# ==========================================
def get_file_type(filename):
    if not filename: return "unknown"
    name = filename.lower()
    if name.endswith(".py"): return "python"
    if name.endswith(".js"): return "javascript"
    if name.endswith(".zip"): return "zip"
    if any(name.endswith(ext) for ext in [".tar", ".tar.gz", ".tgz"]): return "archive"
    return "unknown"

def sanitize_filename(name):
    name = os.path.basename(name or "file")
    name = re.sub(r'[^\w\-\.]', '_', name)
    return name[:80] if name else "uploaded_file"

def safe_extract_zip(zip_ref, extract_dir):
    for member in zip_ref.namelist():
        member_path = os.path.realpath(os.path.join(extract_dir, member))
        if not member_path.startswith(os.path.realpath(extract_dir) + os.sep) and member_path != os.path.realpath(extract_dir):
            raise Exception(f"Unsafe path in archive: {member}")
    zip_ref.extractall(extract_dir)

def safe_extract_tar(tar_ref, extract_dir):
    for member in tar_ref.getmembers():
        member_path = os.path.realpath(os.path.join(extract_dir, member.name))
        if not member_path.startswith(os.path.realpath(extract_dir) + os.sep) and member_path != os.path.realpath(extract_dir):
            raise Exception(f"Unsafe path in archive: {member.name}")
    tar_ref.extractall(extract_dir)

def extract_archive(file_path, extract_dir):
    try:
        if file_path.lower().endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                safe_extract_zip(zip_ref, extract_dir)
        elif file_path.lower().endswith(".tar.gz") or file_path.lower().endswith(".tgz"):
            with tarfile.open(file_path, 'r:gz') as tar_ref:
                safe_extract_tar(tar_ref, extract_dir)
        elif file_path.lower().endswith(".tar"):
            with tarfile.open(file_path, 'r') as tar_ref:
                safe_extract_tar(tar_ref, extract_dir)
        else:
            return False, "Unsupported archive format"
        return True, None
    except Exception as e:
        return False, str(e)

def find_main_file(directory):
    priority_files = [
        "main.py", "bot.py", "app.py", "server.py", "index.py", "script.py",
        "main.js", "bot.js", "app.js", "server.js", "index.js", "script.js"
    ]
    for file_name in priority_files:
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path): return file_path
    for root, dirs, files in os.walk(directory):
        for file_name in priority_files:
            if file_name in files: return os.path.join(root, file_name)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".js"):
                return os.path.join(root, file)
    return None

def install_requirements_from_file(requirements_path, chat_id, file_name):
    try:
        if not os.path.exists(requirements_path): return False, "requirements.txt not found"
        with open(requirements_path, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if not requirements: return True, "No requirements found"
        success_count = 0
        failed_count = 0
        failed_packages = []
        for package in requirements:
            try:
                result = subprocess.run([sys.executable, "-m", "pip", "install", package],
                                        capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_packages.append(package)
            except Exception:
                failed_count += 1
                failed_packages.append(package)
        message = f"📦 Installed {success_count} packages"
        if failed_count > 0:
            message += f", ❌ failed {failed_count}: {', '.join(failed_packages[:5])}"
        return failed_count == 0, message
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

def extract_imports(file_path):
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    imports.add(node.module.split('.')[0])
    except Exception as e:
        logger.error(f"Error parsing imports: {e}")
    return imports

def install_missing_imports(imports, chat_id, file_name):
    missing = []
    for module in imports:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    if not missing:
        return True, "✅ All imports available"
    success_count = 0
    failed_count = 0
    failed_modules = []
    pip_name_map = {'telebot': 'pyTelegramBotAPI', 'PIL': 'Pillow', 'cv2': 'opencv-python',
                    'Crypto': 'pycryptodome', 'bs4': 'beautifulsoup4'}
    for module in missing:
        pip_name = pip_name_map.get(module, module)
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", pip_name],
                                    capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                success_count += 1
            else:
                failed_count += 1
                failed_modules.append(module)
        except Exception:
            failed_count += 1
            failed_modules.append(module)
    message = f"📦 Installed {success_count} modules"
    if failed_count > 0:
        message += f", ❌ failed {failed_count}: {', '.join(failed_modules)}"
    return failed_count == 0, message

# ==========================================
# 🔍 FILE VALIDATOR
# ==========================================
def validate_python_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        if not code.strip():
            return False, "empty", "📄 File is completely empty — no code found!", None

        try:
            ast.parse(code, filename=file_path)
        except SyntaxError as e:
            err_msg = e.msg or "Syntax error"
            line_no = e.lineno
            offset = e.offset
            bad_line = (e.text or "").rstrip()

            detail = f"❌ <b>Syntax Error Detected!</b>\n\n"
            detail += f"📍 <b>Line:</b> <code>{line_no}</code>"
            if offset:
                detail += f", <b>Column:</b> <code>{offset}</code>"
            detail += f"\n\n🐛 <b>Problem:</b> <code>{html_lib.escape(err_msg)}</code>\n"
            if bad_line:
                clean_line = html_lib.escape(bad_line.strip())
                detail += f"\n📝 <b>Your wrong line:</b>\n<code>{clean_line}</code>\n"
            detail += f"\n💡 <b>Solution:</b> Check brackets, quotes, and colons."
            return False, "syntax", detail, line_no

        try:
            compile(code, file_path, 'exec')
        except Exception as e:
            return False, "compile", f"❌ <b>Compile Error:</b>\n<code>{html_lib.escape(str(e))}</code>", None

        warnings = []
        dangerous = ["os.system(", "subprocess.call(", "eval(", "exec("]
        found_danger = [d for d in dangerous if d in code]
        if found_danger:
            warnings.append(f"⚠️ Suspicious code: {', '.join(found_danger)}")

        return True, "ok", "\n".join(warnings), None

    except UnicodeDecodeError:
        return False, "encoding", "❌ File encoding is wrong (must be UTF-8)", None
    except Exception as e:
        return False, "unknown", f"❌ Validation error: <code>{html_lib.escape(str(e))}</code>", None

def validate_javascript_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()

        if not code.strip():
            return False, "empty", "📄 File is completely empty!", None

        try:
            result = subprocess.run(
                ["node", "--check", file_path],
                capture_output=True, text=True, timeout=15
            )
        except FileNotFoundError:
            return True, "skip", "⚠️ Node.js not installed — JS validation skipped", None

        if result.returncode != 0:
            error_output = result.stderr.strip()
            line_match = re.search(r':(\d+)', error_output)
            line_no = int(line_match.group(1)) if line_match else None

            detail = f"❌ <b>JavaScript Error Detected!</b>\n\n"
            if line_no:
                detail += f"📍 <b>Line:</b> <code>{line_no}</code>\n\n"
            detail += f"🐛 <b>Problem:</b>\n<code>{html_lib.escape(error_output[:500])}</code>\n"
            detail += f"\n💡 <b>Solution:</b> Check Node.js syntax."
            return False, "syntax", detail, line_no

        return True, "ok", "", None

    except subprocess.TimeoutExpired:
        return False, "timeout", "⏱️ Validation timeout", None
    except Exception as e:
        return False, "unknown", f"❌ Validation error: <code>{html_lib.escape(str(e))}</code>", None

def validate_file(file_path, file_type):
    if file_type == "python":
        return validate_python_file(file_path)
    elif file_type == "javascript":
        return validate_javascript_file(file_path)
    else:
        return True, "skip", "", None

def check_imports_available(file_path, file_type):
    missing = []
    if file_type != "python":
        return missing
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        tree = ast.parse(code)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    imports.add(node.module.split('.')[0])

        stdlib = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()

        for mod in imports:
            if mod in stdlib:
                continue
            try:
                importlib.import_module(mod)
            except ImportError:
                missing.append(mod)
    except Exception:
        pass
    return missing

def format_validation_error(error_type, error_message, filename):
    header = f"❌ <b>THIS FILE CANNOT RUN!</b> ❌\n"
    header += f"━━━━━━━━━━━━━━━━━━━━\n"
    header += f"📁 <b>File:</b> <code>{html_lib.escape(filename)}</code>\n"
    header += f"━━━━━━━━━━━━━━━━━━━━\n\n"

    if error_type == "empty":
        body = "🚫 <b>Reason:</b> File is empty\n\n💡 Write some code and send again."
    elif error_type == "syntax":
        body = error_message
    elif error_type == "encoding":
        body = "🚫 <b>Reason:</b> Encoding problem\n\n💡 Save the file as UTF-8 and send again."
    elif error_type == "timeout":
        body = "🚫 <b>Reason:</b> File is too large\n\n💡 Make it smaller and send again."
    else:
        body = error_message

    footer = "\n\n━━━━━━━━━━━━━━━━━━━━\n"
    footer += "🛠️ <b>Fix the error and upload again.</b>\n"
    footer += f"📞 Help: @{OWNER_USERNAME}"

    return header + body + footer

def format_crash_report(original_name, exit_code, log_path):
    error_snippet = ""
    log_lower = ""
    try:
        if os.path.exists(log_path):
            with open(log_path, 'r', errors='ignore') as lf:
                log_content = lf.read()
            log_lower = log_content.lower()
            if log_content.strip():
                tail = log_content[-1500:]
                error_snippet = html_lib.escape(tail)
            else:
                error_snippet = "_(Log is empty — script printed nothing)_"
    except Exception as le:
        error_snippet = f"_(Log read error: {le})_"

    friendly_hint = ""
    if "modulenotfounderror" in log_lower or "no module named" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Python module missing\n🛠️ <b>Fix:</b> Add all modules in <code>requirements.txt</code>"
    elif "syntaxerror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Syntax error\n🛠️ <b>Fix:</b> Check code syntax"
    elif "importerror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Import problem\n🛠️ <b>Fix:</b> Check module name"
    elif "indentationerror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Wrong indentation\n🛠️ <b>Fix:</b> Check spaces/tabs"
    elif "filenotfounderror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> File missing\n🛠️ <b>Fix:</b> Check file path"
    elif "keyerror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Dictionary key missing\n🛠️ <b>Fix:</b> Check key name"
    elif "nameerror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Variable not defined\n🛠️ <b>Fix:</b> Check variable name"
    elif "typeerror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Wrong data type\n🛠️ <b>Fix:</b> Check function arguments"
    elif "valueerror" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Wrong value\n🛠️ <b>Fix:</b> Check input values"
    elif "token" in log_lower and ("invalid" in log_lower or "unauthorized" in log_lower):
        friendly_hint = "💡 <b>Reason:</b> Bot token invalid\n🛠️ <b>Fix:</b> Get new token from BotFather"
    elif "eaddrinuse" in log_lower or "address already in use" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Port already in use\n🛠️ <b>Fix:</b> Use a different port"
    elif "connectionerror" in log_lower or "connection refused" in log_lower:
        friendly_hint = "💡 <b>Reason:</b> Connection failed\n🛠️ <b>Fix:</b> Check internet/URL"
    else:
        friendly_hint = "💡 <b>Tip:</b> Check exact error line in log"

    return (
        f"❌ <b>FILE CRASHED!</b> ❌\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📁 <b>File:</b> <code>{html_lib.escape(original_name)}</code>\n"
        f"📛 <b>Exit Code:</b> <code>{exit_code}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🐛 <b>Error Details:</b>\n"
        f"<pre>{error_snippet}</pre>\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{friendly_hint}\n\n"
        f"🛠️ Fix the file and upload again.\n"
        f"📞 Help: @{OWNER_USERNAME}"
    )

# ==========================================
# 📡 SERVER PING — Photo-Style
# ==========================================
def get_server_ping_info():
    try:
        start = time.time()
        try:
            bot.get_me()
            telegram_latency = int((time.time() - start) * 1000)
        except:
            telegram_latency = 0

        cpu = psutil.cpu_percent(interval=0.1)
        if cpu >= 80:
            load_status = "🔴 High"
        elif cpu >= 50:
            load_status = "🟡 Medium"
        else:
            load_status = "🟢 Low"

        uptime_td = datetime.utcnow() - START_TIME
        days = uptime_td.days
        hours, remainder = divmod(uptime_td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            uptime_str = f"{days}d {hours}h {minutes}m"
        else:
            uptime_str = f"{hours}h {minutes}m"

        with proc_lock:
            bots_running = len(processes)

        docker_status = "❌"
        try:
            docker_check = subprocess.run(["docker", "info"], capture_output=True, timeout=3)
            if docker_check.returncode == 0:
                docker_status = "✅"
        except:
            docker_status = "❌"

        memory = psutil.virtual_memory().percent
        all_ok = True
        issues = []
        if telegram_latency == 0:
            all_ok = False
            issues.append("Telegram latency")
        if cpu >= 90:
            all_ok = False
            issues.append("High CPU")
        if memory >= 90:
            all_ok = False
            issues.append("High Memory")

        return {
            "telegram_latency": telegram_latency,
            "load_status": load_status,
            "cpu": cpu,
            "uptime": uptime_str,
            "bots_running": bots_running,
            "docker_status": docker_status,
            "all_ok": all_ok,
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Server ping error: {e}")
        return None

def send_server_ping(chat_id, message_id=None):
    info = get_server_ping_info()
    if not info:
        bot.send_message(chat_id, "❌ Server ping failed")
        return

    if info["all_ok"]:
        status_line = "✅ All Systems Operational"
    else:
        status_line = f"⚠️ Issues: {', '.join(info['issues'])}"

    text = (
        f"⚡ <b>𝐒𝐄𝐑𝐕𝐄𝐑 𝐏𝐈𝐍𝐆</b> ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 Telegram Latency: <b>{info['telegram_latency']} ms</b>\n"
        f"🖥️ Server Load: {info['load_status']}\n"
        f"⏱️ Uptime: <b>{info['uptime']}</b>\n"
        f"🤖 Bots Running: <b>{info['bots_running']}</b>\n"
        f"🐳 Docker: {info['docker_status']}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{status_line}"
    )

    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("🔄 𝐏𝐢𝐧𝐠 𝐀𝐠𝐚𝐢𝐧", callback_data="server_ping_again"))

    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb, parse_mode="HTML")
        except:
            bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
    else:
        bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")

# ==========================================
# 🧠 AUTO MEMORY MANAGER
# ==========================================
def kill_oldest_process():
    try:
        with proc_lock:
            if not processes:
                return None
            oldest_file_id = min(processes.keys(),
                                 key=lambda x: processes[x].get('started_at', ''))
            file_record = get_file_record(oldest_file_id)
            file_name = file_record["orig_name"] if file_record else f"File #{oldest_file_id}"
            user_id = file_record["user_id"] if file_record else None

        stop_file_process(oldest_file_id)

        if file_record:
            try:
                if os.path.isdir(file_record["path"]):
                    shutil.rmtree(file_record["path"], ignore_errors=True)
                elif os.path.exists(file_record["path"]):
                    os.remove(file_record["path"])
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
            remove_file_record(oldest_file_id)

        if user_id:
            try:
                bot.send_message(user_id,
                    f"⚠️ <b>𝐀𝐮𝐭𝐨 𝐂𝐥𝐞𝐚𝐧𝐮𝐩!</b>\n\n"
                    f"Your file <b>{html_lib.escape(file_name)}</b> was automatically stopped and removed to free server RAM.\n\n"
                    f"💡 Server was overloaded. Please try again later.",
                    parse_mode="HTML")
            except:
                pass

        logger.info(f"🧠 Auto-killed oldest process: {file_name}")
        return file_name
    except Exception as e:
        logger.error(f"kill_oldest_process error: {e}")
        return None

def auto_memory_manager():
    while not STOP_EVENT.is_set():
        try:
            memory = psutil.virtual_memory().percent
            if memory >= RAM_AUTO_KILL_THRESHOLD:
                with proc_lock:
                    has_process = len(processes) > 0
                if has_process:
                    killed = kill_oldest_process()
                    if killed:
                        try:
                            bot.send_message(ADMIN_ID,
                                f"🧠 <b>Auto Memory Manager</b>\n\n"
                                f"⚠️ RAM reached <b>{memory:.1f}%</b>\n"
                                f"🗑 Removed oldest file: <b>{html_lib.escape(killed)}</b>",
                                parse_mode="HTML")
                        except:
                            pass
        except Exception as e:
            logger.error(f"auto_memory_manager error: {e}")
        time.sleep(RAM_CHECK_INTERVAL)

def cleanup_old_logs():
    try:
        cutoff = time.time() - (LOG_RETENTION_DAYS * 86400)
        deleted = 0
        for log_file in os.listdir(LOGS_DIR):
            log_path = os.path.join(LOGS_DIR, log_file)
            try:
                if os.path.isfile(log_path) and os.path.getmtime(log_path) < cutoff:
                    os.remove(log_path)
                    deleted += 1
            except:
                pass
        if deleted > 0:
            logger.info(f"🗑 Deleted {deleted} old logs")
    except Exception as e:
        logger.error(f"cleanup_old_logs error: {e}")

def cleanup_old_files():
    try:
        cutoff = time.time() - (FILE_RETENTION_DAYS * 86400)
        deleted = 0
        for user_dir in os.listdir(UPLOADS_DIR):
            user_path = os.path.join(UPLOADS_DIR, user_dir)
            if not os.path.isdir(user_path):
                continue
            for file_name in os.listdir(user_path):
                file_path = os.path.join(user_path, file_name)
                try:
                    if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                        os.remove(file_path)
                        deleted += 1
                except:
                    pass
        if deleted > 0:
            logger.info(f"🗑 Deleted {deleted} old files")
    except Exception as e:
        logger.error(f"cleanup_old_files error: {e}")

def cleanup_temp():
    try:
        cutoff = time.time() - 86400
        for temp_dir in os.listdir(TEMP_DIR):
            temp_path = os.path.join(TEMP_DIR, temp_dir)
            try:
                if os.path.isdir(temp_path) and os.path.getmtime(temp_path) < cutoff:
                    shutil.rmtree(temp_path, ignore_errors=True)
            except:
                pass
    except Exception as e:
        logger.error(f"cleanup_temp error: {e}")

def auto_cleaner():
    while not STOP_EVENT.is_set():
        try:
            cleanup_old_logs()
            cleanup_old_files()
            cleanup_temp()
        except Exception as e:
            logger.error(f"auto_cleaner error: {e}")
        time.sleep(86400)

def garbage_collector():
    while not STOP_EVENT.is_set():
        try:
            gc.collect()
        except Exception as e:
            logger.error(f"gc error: {e}")
        time.sleep(GC_INTERVAL)

# ==========================================
# 🤖 BOT INIT
# ==========================================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def is_user_joined(user_id):
    if user_id == ADMIN_ID: return True
    try:
        chat_member = bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking membership for {user_id}: {e}")
        return False

def force_join_kb():
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📢 𝐉𝐨𝐢𝐧 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", url=CHANNEL_LINK))
    kb.row(InlineKeyboardButton("✅ 𝐕𝐄𝐑𝐈𝐅𝐈𝐄𝐃", callback_data="verified_check"))
    return kb

def _graceful_shutdown(signum=None, frame=None):
    try:
        STOP_EVENT.set()
        try:
            bot.stop_polling()
        except Exception:
            pass
        logger.info("🛑 Shutdown signal received.")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    raise SystemExit(0)

signal.signal(signal.SIGINT, _graceful_shutdown)
signal.signal(signal.SIGTERM, _graceful_shutdown)

# ==========================================
# 🎨 ROYAL PREMIUM MENU
# ==========================================
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton("📢 𝐔𝐩𝐝𝐚𝐭𝐞𝐬 𝐂𝐡𝐚𝐧𝐧𝐞𝐥"))
    kb.add(KeyboardButton("📤 𝐔𝐩𝐥𝐨𝐚𝐝 𝐅𝐢𝐥𝐞"), KeyboardButton("📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬"))
    kb.add(KeyboardButton("⚡ 𝐁𝐨𝐭 𝐒𝐩𝐞𝐞𝐝"), KeyboardButton("📊 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬"))
    kb.add(KeyboardButton("🎁 𝐑𝐞𝐟𝐞𝐫 & 𝐄𝐚𝐫𝐧"), KeyboardButton("💎 𝐁𝐮𝐲 𝐏𝐫𝐞𝐦𝐢𝐮𝐦"))
    kb.add(KeyboardButton("🎬 𝐕𝐢𝐝𝐞𝐨 𝐓𝐮𝐭𝐨𝐫𝐢𝐚𝐥𝐬"), KeyboardButton("📡 𝐒𝐞𝐫𝐯𝐞𝐫 𝐏𝐢𝐧𝐠"))
    kb.add(KeyboardButton("📞 𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐎𝐰𝐧𝐞𝐫"))
    return kb

def file_actions_kb(file_id, is_running=False):
    kb = InlineKeyboardMarkup()
    if is_running:
        kb.row(InlineKeyboardButton("⏹ 𝐒𝐭𝐨𝐩", callback_data=f"stop:{file_id}"),
               InlineKeyboardButton("🔁 𝐑𝐞𝐬𝐭𝐚𝐫𝐭", callback_data=f"restart:{file_id}"))
    else:
        kb.row(InlineKeyboardButton("▶️ 𝐒𝐭𝐚𝐫𝐭", callback_data=f"start:{file_id}"),
               InlineKeyboardButton("🔁 𝐑𝐞𝐬𝐭𝐚𝐫𝐭", callback_data=f"restart:{file_id}"))
    kb.row(InlineKeyboardButton("🗑 𝐃𝐞𝐥𝐞𝐭𝐞", callback_data=f"delete:{file_id}"),
           InlineKeyboardButton("📄 𝐋𝐨𝐠𝐬", callback_data=f"logs:{file_id}"))
    kb.row(InlineKeyboardButton("⬅️ 𝐁𝐚𝐜𝐤", callback_data="back_to_files"))
    return kb

def admin_approval_kb(file_id):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("✅ 𝐀𝐩𝐩𝐫𝐨𝐯𝐞", callback_data=f"approve:{file_id}"),
           InlineKeyboardButton("❌ 𝐑𝐞𝐣𝐞𝐜𝐭", callback_data=f"reject:{file_id}"))
    return kb

# ==========================================
# 👑 ADMIN PANEL
# ==========================================
@bot.message_handler(func=lambda m: m.text and m.text.strip().lower() in ["admin", "/admin"])
def admin_commands_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ This is only for Admin.")
        return

    text = (
        "👑 <b>𝐀𝐃𝐌𝐈𝐍 𝐏𝐀𝐍𝐄𝐋</b> 👑\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>Select an option below:</b>\n\n"
        "💰 <b>Change Prices</b>\n"
        "📝 <b>Change Plan Names</b>\n"
        "🎬 <b>YouTube Link</b>\n"
        "📢 <b>Broadcast</b>\n"
        "📊 <b>View Plans</b>\n"
    )

    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("💰 𝐂𝐡𝐚𝐧𝐠𝐞 𝐏𝐫𝐢𝐜𝐞", callback_data="admin_change_price"),
        InlineKeyboardButton("📝 𝐂𝐡𝐚𝐧𝐠𝐞 𝐍𝐚𝐦𝐞", callback_data="admin_change_name")
    )
    kb.row(
        InlineKeyboardButton("🎬 𝐘𝐨𝐮𝐓𝐮𝐛𝐞 𝐋𝐢𝐧𝐤", callback_data="admin_youtube"),
        InlineKeyboardButton("📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭", callback_data="admin_broadcast_mode")
    )
    kb.row(
        InlineKeyboardButton("📊 𝐕𝐢𝐞𝐰 𝐏𝐥𝐚𝐧𝐬", callback_data="admin_viewplans"),
        InlineKeyboardButton("📋 𝐀𝐥𝐥 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬", callback_data="admin_all_cmds")
    )

    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data == "admin_change_price")
def admin_change_price_btn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "💰 Select Plan")
    kb = InlineKeyboardMarkup()
    for key, plan in PREMIUM_PLANS.items():
        kb.row(InlineKeyboardButton(f"{plan['name']} — {plan['price']}", callback_data=f"chg_price:{key}"))
    kb.row(InlineKeyboardButton("⬅️ 𝐁𝐚𝐜𝐤", callback_data="admin_back"))
    try:
        bot.edit_message_text("💰 <b>Change Price</b>\n\n👇 Select the plan:", chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, "💰 <b>Change Price</b>\n\n👇 Select the plan:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("chg_price:"))
def chg_price_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    key = call.data.split(":")[1]
    plan = PREMIUM_PLANS.get(key)
    if not plan:
        bot.answer_callback_query(call.id, "❌ Invalid plan", show_alert=True)
        return
    bot.answer_callback_query(call.id, "✍️ Type new price")
    msg = bot.send_message(
        call.message.chat.id,
        f"💰 <b>Change Price — {plan['name']}</b>\n\n"
        f"📦 Current: <b>{plan['price']}</b>\n\n"
        f"✍️ <b>Type new price:</b>\nExample: <code>₹99</code>\n"
        f"❌ Type <code>cancel</code> to cancel"
    )
    bot.register_next_step_handler(msg, save_new_price, key)

def save_new_price(message, key):
    if message.text and message.text.strip().lower() == "cancel":
        bot.send_message(message.chat.id, "❌ Cancelled.")
        return
    if not message.text:
        bot.send_message(message.chat.id, "⚠️ Please send text.")
        return
    new_price = message.text.strip()
    old_price = PREMIUM_PLANS[key]["price"]
    PREMIUM_PLANS[key]["price"] = new_price
    try:
        PREMIUM_PLANS[key]["amount"] = float(new_price.replace("₹", "").strip())
    except:
        pass
    bot.send_message(message.chat.id,
        f"✅ <b>Price Updated!</b>\n\n"
        f"📦 Plan: <b>{PREMIUM_PLANS[key]['name']}</b>\n"
        f"💰 Old: {old_price}\n"
        f"💰 New: <b>{new_price}</b>")

@bot.callback_query_handler(func=lambda call: call.data == "admin_change_name")
def admin_change_name_btn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "📝 Select Plan")
    kb = InlineKeyboardMarkup()
    for key, plan in PREMIUM_PLANS.items():
        kb.row(InlineKeyboardButton(f"{plan['name']}", callback_data=f"chg_name:{key}"))
    kb.row(InlineKeyboardButton("⬅️ 𝐁𝐚𝐜𝐤", callback_data="admin_back"))
    try:
        bot.edit_message_text("📝 <b>Change Plan Name</b>\n\n👇 Select the plan:", chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, "📝 <b>Change Plan Name</b>\n\n👇 Select the plan:", reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("chg_name:"))
def chg_name_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    key = call.data.split(":")[1]
    plan = PREMIUM_PLANS.get(key)
    if not plan:
        bot.answer_callback_query(call.id, "❌ Invalid plan", show_alert=True)
        return
    bot.answer_callback_query(call.id, "✍️ Type new name")
    msg = bot.send_message(
        call.message.chat.id,
        f"📝 <b>Change Name — {plan['name']}</b>\n\n"
        f"📦 Current: <b>{plan['name']}</b>\n\n"
        f"✍️ <b>Type new name:</b>\n"
        f"❌ Type <code>cancel</code> to cancel"
    )
    bot.register_next_step_handler(msg, save_new_name, key)

def save_new_name(message, key):
    if message.text and message.text.strip().lower() == "cancel":
        bot.send_message(message.chat.id, "❌ Cancelled.")
        return
    if not message.text:
        bot.send_message(message.chat.id, "⚠️ Please send text.")
        return
    new_name = message.text.strip()
    old_name = PREMIUM_PLANS[key]["name"]
    PREMIUM_PLANS[key]["name"] = new_name
    bot.send_message(message.chat.id,
        f"✅ <b>Plan Name Updated!</b>\n\n"
        f"🔑 Key: <code>{key}</code>\n"
        f"📦 Old: {old_name}\n"
        f"📦 New: <b>{new_name}</b>")

@bot.callback_query_handler(func=lambda call: call.data == "admin_youtube")
def admin_youtube_btn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "🎬 Change YouTube Link")
    msg = bot.send_message(
        call.message.chat.id,
        f"🎬 <b>Change YouTube Link</b>\n\n"
        f"🔗 Current:\n<code>{YOUTUBE_CHANNEL}</code>\n\n"
        f"✍️ <b>Send new link:</b>\nExample: <code>https://youtube.com/@YourChannel</code>\n"
        f"❌ Type <code>cancel</code> to cancel"
    )
    bot.register_next_step_handler(msg, save_new_youtube)

def save_new_youtube(message):
    global YOUTUBE_CHANNEL
    if message.text and message.text.strip().lower() == "cancel":
        bot.send_message(message.chat.id, "❌ Cancelled.")
        return
    if not message.text:
        bot.send_message(message.chat.id, "⚠️ Please send text.")
        return
    new_link = message.text.strip()
    if not (new_link.startswith("http://") or new_link.startswith("https://")):
        bot.send_message(message.chat.id, "❌ Invalid link.")
        return
    old_link = YOUTUBE_CHANNEL
    YOUTUBE_CHANNEL = new_link
    bot.send_message(message.chat.id,
        f"✅ <b>YouTube Link Updated!</b>\n\n"
        f"🔗 Old: {old_link}\n"
        f"🔗 New: <b>{new_link}</b>")

@bot.callback_query_handler(func=lambda call: call.data == "admin_broadcast_mode")
def admin_broadcast_mode_btn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "📢 Broadcast Mode ON")
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("❌ 𝐂𝐚𝐧𝐜𝐞𝐥", callback_data="cancel_broadcast"))
    msg = bot.send_message(
        call.message.chat.id,
        "📢 <b>𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭 𝐌𝐨𝐝𝐞</b>\n\n"
        "✍️ <b>Send any message, it will go to all users!</b>\n\n"
        "✅ Text, Photo, Video, Document — anything\n\n"
        "👇 <b>Send your message now:</b>",
        reply_markup=kb
    )
    bot.register_next_step_handler(msg, send_broadcast_message)

def send_broadcast_message(message):
    if message.text and message.text.strip().lower() in ["/cancel", "cancel"]:
        bot.send_message(message.chat.id, "❌ Broadcast cancelled.")
        return

    cur = conn.cursor()
    cur.execute("SELECT DISTINCT user_id FROM users")
    users = cur.fetchall()
    if not users:
        bot.send_message(message.chat.id, "❌ No users found.")
        return

    total = len(users)
    success = 0
    failed = 0
    status_msg = bot.send_message(message.chat.id, f"📢 <b>Broadcasting to {total} users...</b>")

    for row in users:
        try:
            bot.copy_message(chat_id=row[0], from_chat_id=message.chat.id, message_id=message.message_id)
            success += 1
            time.sleep(0.05)
        except Exception:
            failed += 1

    try:
        bot.edit_message_text(
            f"✅ <b>Broadcast Complete</b>\n\n"
            f"📤 Sent: <b>{success}</b>\n"
            f"❌ Failed: <b>{failed}</b>\n"
            f"👥 Total: <b>{total}</b>",
            chat_id=message.chat.id, message_id=status_msg.message_id
        )
    except:
        bot.send_message(message.chat.id, f"✅ Done. Sent: {success}, Failed: {failed}")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_broadcast")
def cancel_broadcast_handler(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "❌ Cancelled")
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        pass
    bot.send_message(call.message.chat.id, "❌ <b>Broadcast cancelled.</b>")

@bot.callback_query_handler(func=lambda call: call.data == "admin_viewplans")
def admin_viewplans_btn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "📊 Showing Plans...")
    text = "💎 <b>Current Premium Plans</b>\n\n"
    for key, plan in PREMIUM_PLANS.items():
        text += (f"🔑 Key: <code>{key}</code>\n"
                 f"📦 Name: <b>{plan['name']}</b>\n"
                 f"💰 Price: <b>{plan['price']}</b>\n"
                 f"⏳ Days: <b>{plan['days']}</b>\n\n")
    text += f"🎬 YouTube: <code>{YOUTUBE_CHANNEL}</code>"
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin_all_cmds")
def admin_all_cmds_btn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "📋 All Commands")
    text = ("👑 <b>All Admin Commands</b>\n\n"
            "💰 <code>/setprice 1m ₹49</code>\n"
            "📝 <code>/setname 1m 30 Days</code>\n"
            "📊 <code>/viewplans</code>\n\n"
            "💡 Or type <code>admin</code> for buttons!")
    bot.send_message(call.message.chat.id, text)

@bot.callback_query_handler(func=lambda call: call.data == "admin_back")
def admin_back_btn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Only Admin", show_alert=True)
        return
    bot.answer_callback_query(call.id, "⬅️ Back")
    text = (
        "👑 <b>ADMIN PANEL</b>\n\n"
        "👇 <b>Select an option below:</b>\n"
    )
    kb = InlineKeyboardMarkup()
    kb.row(
        InlineKeyboardButton("💰 𝐂𝐡𝐚𝐧𝐠𝐞 𝐏𝐫𝐢𝐜𝐞", callback_data="admin_change_price"),
        InlineKeyboardButton("📝 𝐂𝐡𝐚𝐧𝐠𝐞 𝐍𝐚𝐦𝐞", callback_data="admin_change_name")
    )
    kb.row(
        InlineKeyboardButton("🎬 𝐘𝐨𝐮𝐓𝐮𝐛𝐞 𝐋𝐢𝐧𝐤", callback_data="admin_youtube"),
        InlineKeyboardButton("📢 𝐁𝐫𝐨𝐚𝐝𝐜𝐚𝐬𝐭", callback_data="admin_broadcast_mode")
    )
    kb.row(
        InlineKeyboardButton("📊 𝐕𝐢𝐞𝐰 𝐏𝐥𝐚𝐧𝐬", callback_data="admin_viewplans"),
        InlineKeyboardButton("📋 𝐀𝐥𝐥 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬", callback_data="admin_all_cmds")
    )
    try:
        bot.edit_message_text(text, chat_id=call.message.chat.id,
                              message_id=call.message.message_id, reply_markup=kb)
    except:
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

@bot.message_handler(commands=['viewplans'])
def view_plans_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only for Admin.")
        return
    text = "💎 <b>Current Premium Plans</b>\n\n"
    for key, plan in PREMIUM_PLANS.items():
        text += (f"🔑 Key: <code>{key}</code>\n"
                 f"📦 Name: <b>{plan['name']}</b>\n"
                 f"💰 Price: <b>{plan['price']}</b>\n"
                 f"⏳ Days: <b>{plan['days']}</b>\n\n")
    bot.reply_to(message, text)

@bot.message_handler(commands=['setprice'])
def set_price_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only for Admin.")
        return
    args = message.text.replace("/setprice", "", 1).strip().split()
    if len(args) < 2:
        bot.reply_to(message, "💰 <b>Usage:</b> <code>/setprice &lt;key&gt; &lt;new_price&gt;</code>")
        return
    key = args[0].lower()
    new_price = args[1]
    if key not in PREMIUM_PLANS:
        bot.reply_to(message, f"❌ Invalid key. Available: {', '.join(PREMIUM_PLANS.keys())}")
        return
    old_price = PREMIUM_PLANS[key]["price"]
    PREMIUM_PLANS[key]["price"] = new_price
    try:
        PREMIUM_PLANS[key]["amount"] = float(new_price.replace("₹", "").strip())
    except:
        pass
    bot.reply_to(message, f"✅ <b>Price Updated!</b>\n\n🔑 Key: <code>{key}</code>\n💰 Old: {old_price}\n💰 New: <b>{new_price}</b>")

@bot.message_handler(commands=['setname'])
def set_name_handler(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only for Admin.")
        return
    parts = message.text.replace("/setname", "", 1).strip().split(" ", 1)
    if len(parts) < 2:
        bot.reply_to(message, "📝 <b>Usage:</b> <code>/setname &lt;key&gt; &lt;new_name&gt;</code>")
        return
    key = parts[0].lower()
    new_name = parts[1]
    if key not in PREMIUM_PLANS:
        bot.reply_to(message, f"❌ Invalid key.")
        return
    old_name = PREMIUM_PLANS[key]["name"]
    PREMIUM_PLANS[key]["name"] = new_name
    bot.reply_to(message, f"✅ <b>Updated!</b>\n\n🔑 Key: <code>{key}</code>\n📦 Old: {old_name}\n📦 New: <b>{new_name}</b>")

# ==========================================
# 🚀 START HANDLER
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    user = message.from_user
    user_id = user.id

    if message.text and len(message.text.split()) > 1:
        arg = message.text.split()[1]
        if arg.startswith("ref_"):
            try:
                referrer_id = int(arg.replace("ref_", ""))
                if referrer_id != user_id and referrer_id != ADMIN_ID:
                    if not has_been_referred(user_id):
                        success = add_referral(referrer_id, user_id, user.username or "", user.first_name or "User")
                        if success:
                            try:
                                bot.send_message(referrer_id,
                                    f"🎉 <b>New Referral!</b>\n\n"
                                    f"👤 <b>{html_lib.escape(user.first_name or 'User')}</b> joined!\n"
                                    f"📊 Total: <b>{get_referral_count(referrer_id)}</b>")
                            except:
                                pass
            except:
                pass

    if not is_user_joined(user_id):
        lock_text = (
            "🔒 <b>𝐀𝐂𝐂𝐄𝐒𝐒 𝐋𝐎𝐂𝐊𝐄𝐃</b> 🔒\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "To unlock, first join our channel 👇\n\n"
            "1️⃣ Tap <b>Join Channel</b>\n"
            "2️⃣ After joining, tap <b>VERIFIED</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ Leaving will lock access again."
        )
        bot.send_message(message.chat.id, lock_text, reply_markup=force_join_kb())
        return

    with db_lock:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO users (user_id, username, joined_at, last_seen) VALUES (?, ?, ?, ?)",
                    (user_id, user.username or "", datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        conn.commit()

    files = list_user_files(user_id)
    limit_text = "∞" if user_id == ADMIN_ID else str(get_effective_file_limit(user_id))
    ref_count = get_referral_count(user_id)
    prem_status = "💎 PREMIUM" if is_premium(user_id) else "🆓 FREE"

    welcome_text = (
        "✨━━━━━━━━━━━━━━━━━━━━✨\n"
        "   👑 <b>𝐀𝐉𝐀𝐘 𝐇𝐎𝐒𝐓𝐈𝐍𝐆 𝐁𝐎𝐓</b> 👑\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨\n\n"
        f"🌟 Hello <b>{html_lib.escape(user.first_name or 'User')}</b>!\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📂 Files: <b>{len(files)}/{limit_text}</b>\n"
        f"🎁 Referrals: <b>{ref_count}</b>\n"
        f"💎 Plan: <b>{prem_status}</b>\n\n"
        "⚡ <b>𝐏𝐨𝐰𝐞𝐫𝐟𝐮𝐥 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬</b> ⚡\n"
        "🐍 Host Python &amp; JS Scripts\n"
        "📦 Auto-Install Dependencies\n"
        "🔍 Smart Error Detection\n"
        "📡 Live Server Ping\n"
        "🧠 Auto Memory Manager\n"
        "⏰ 24/7 Non-Stop Hosting\n"
        "🎁 Refer &amp; Earn Rewards\n\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨\n"
        "   🚀 <b>𝐓𝐚𝐩 𝐁𝐞𝐥𝐨𝐰 𝐓𝐨 𝐒𝐭𝐚𝐫𝐭</b> 🚀\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_kb())

@bot.callback_query_handler(func=lambda call: call.data == "verified_check")
def verified_check_handler(call):
    user_id = call.from_user.id
    if is_user_joined(user_id):
        bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        user = call.from_user
        files = list_user_files(user_id)
        limit_text = "∞" if user_id == ADMIN_ID else str(get_effective_file_limit(user_id))
        ref_count = get_referral_count(user_id)
        prem_status = "💎 PREMIUM" if is_premium(user_id) else "🆓 FREE"
        welcome_text = (
            "✨━━━━━━━━━━━━━━━━━━━━✨\n"
            "   👑 <b>𝐀𝐉𝐀𝐘 𝐇𝐎𝐒𝐓𝐈𝐍𝐆 𝐁𝐎𝐓</b> 👑\n"
            "✨━━━━━━━━━━━━━━━━━━━━✨\n\n"
            f"🌟 Hello <b>{html_lib.escape(user.first_name or 'User')}</b>!\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"📂 Files: <b>{len(files)}/{limit_text}</b>\n"
            f"🎁 Referrals: <b>{ref_count}</b>\n"
            f"💎 Plan: <b>{prem_status}</b>\n\n"
            "✨━━━━━━━━━━━━━━━━━━━━✨\n"
            "   🚀 <b>𝐓𝐚𝐩 𝐁𝐞𝐥𝐨𝐰 𝐓𝐨 𝐒𝐭𝐚𝐫𝐭</b> 🚀\n"
            "✨━━━━━━━━━━━━━━━━━━━━✨"
        )
        bot.send_message(call.message.chat.id, welcome_text, reply_markup=main_menu_kb())
    else:
        bot.answer_callback_query(call.id, "❌ Join channel first!", show_alert=True)

# ==========================================
# 📡 SERVER PING HANDLER
# ==========================================
@bot.message_handler(func=lambda m: m.text == "📡 𝐒𝐞𝐫𝐯𝐞𝐫 𝐏𝐢𝐧𝐠" or m.text == "📡 Server Ping")
def server_ping_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    send_server_ping(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "server_ping_again")
def server_ping_again_handler(call):
    bot.answer_callback_query(call.id, "🔄 Pinging...")
    send_server_ping(call.message.chat.id, call.message.message_id)

# ==========================================
# 🎬 VIDEO TUTORIALS
# ==========================================
@bot.message_handler(func=lambda m: m.text == "🎬 𝐕𝐢𝐝𝐞𝐨 𝐓𝐮𝐭𝐨𝐫𝐢𝐚𝐥𝐬" or m.text == "🎬 Video Tutorials")
def video_tutorials_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📺 𝐎𝐩𝐞𝐧 𝐘𝐨𝐮𝐓𝐮𝐛𝐞 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", url=YOUTUBE_CHANNEL))
    bot.send_message(message.chat.id,
        "🎬 <b>𝐕𝐢𝐝𝐞𝐨 𝐓𝐮𝐭𝐨𝐫𝐢𝐚𝐥𝐬</b>\n\n👇 Tap below:",
        reply_markup=kb, disable_web_page_preview=True)

# ==========================================
# 💎 PREMIUM BUY
# ==========================================
@bot.message_handler(func=lambda m: m.text == "💎 𝐁𝐮𝐲 𝐏𝐫𝐞𝐦𝐢𝐮𝐦" or m.text == "💎 Buy Premium")
def buy_premium_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return

    user_id = message.from_user.id

    if is_premium(user_id):
        expiry = get_premium_expiry(user_id)
        plan_name = get_premium_plan_name(user_id) or "Premium"
        bot.send_message(message.chat.id,
            f"💎 <b>You are already Premium!</b>\n\n"
            f"📦 Plan: <b>{plan_name}</b>\n"
            f"📅 Expires: <code>{expiry[:16] if expiry else 'N/A'}</code>")
        return

    plan_text = (
        "✨━━━━━━━━━━━━━━━━━━━━✨\n"
        "   💎 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐌𝐄𝐌𝐁𝐄𝐑𝐒𝐇𝐈𝐏</b> 💎\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨\n\n"
        "👑 <b>𝐋𝐗 𝐇𝐎𝐒𝐓𝐈𝐍𝐆 𝐏𝐑𝐄𝐌𝐈𝐔𝐌</b> 👑\n\n"
        "⚡ Instant UPI Payment — Scan &amp; Go!\n"
        "🎁 Unlimited Files • No Approval\n"
        "🚀 High-Speed Server Access\n"
        "💎 Priority Support 24/7\n\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨\n"
        "   👇 <b>𝐂𝐡𝐨𝐨𝐬𝐞 𝐘𝐨𝐮𝐫 𝐏𝐥𝐚𝐧</b> 👇\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨"
    )

    kb = InlineKeyboardMarkup()
    for key, plan in PREMIUM_PLANS.items():
        kb.row(InlineKeyboardButton(f"{plan['name']} — {plan['price']}", callback_data=f"premium:{key}"))
    bot.send_message(message.chat.id, plan_text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: call.data.startswith("premium:"))
def premium_plan_handler(call):
    plan_key = call.data.split(":")[1]
    plan = PREMIUM_PLANS.get(plan_key)
    if not plan:
        bot.answer_callback_query(call.id, "❌ Invalid plan", show_alert=True)
        return

    user_id = call.from_user.id
    bot.answer_callback_query(call.id, "💳 Creating order...")

    order = create_payment_order(user_id, plan_key)
    if not order:
        bot.send_message(call.message.chat.id, "❌ Failed to create order.")
        return

    caption = (
        "✨━━━━━━━━━━━━━━━━━━━━✨\n"
        "   💎 <b>𝐏𝐑𝐄𝐌𝐈𝐔𝐌 𝐏𝐀𝐘𝐌𝐄𝐍𝐓</b> 💎\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨\n\n"
        f"📦 Plan: <b>{plan['name']}</b>\n"
        f"💰 Amount: <b>₹{order.payable_amount}</b>\n"
        f"⏳ Duration: <b>{plan['days']} days</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📸 <b>How to Pay:</b>\n"
        "1️⃣ Tap '💳 Pay Now' below\n"
        "2️⃣ Choose UPI app\n"
        f"3️⃣ Pay <b>₹{order.payable_amount}</b>\n"
        "4️⃣ Bot will auto-verify ✅\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🆔 Order ID: <code>{order.order_id}</code>"
    )

    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("💳 𝐏𝐚𝐲 𝐍𝐨𝐰", url=order.upi_intent))
    kb.row(InlineKeyboardButton("🔄 𝐂𝐡𝐞𝐜𝐤 𝐏𝐚𝐲𝐦𝐞𝐧𝐭", callback_data=f"auto_check:{order.order_id}"))

    try:
        bot.send_photo(call.message.chat.id, order.qr_url, caption=caption, reply_markup=kb)
    except Exception as e:
        logger.error(f"QR send error: {e}")
        bot.send_message(call.message.chat.id, caption, reply_markup=kb)

    threading.Thread(target=auto_verify_payment,
                     args=(call.message.chat.id, user_id, order.order_id, plan_key),
                     daemon=True).start()

def auto_verify_payment(chat_id, user_id, order_id, plan_key):
    plan = PREMIUM_PLANS.get(plan_key)
    if not plan: return
    max_attempts = 60
    attempts = 0

    while attempts < max_attempts:
        time.sleep(5)
        attempts += 1
        result = verify_payment(order_id)
        success, info = is_payment_success(result)

        if success:
            activate_premium(user_id, plan_key)
            expiry = get_premium_expiry(user_id)
            utr = info.get("utr", "N/A")

            try:
                with db_lock:
                    cur = conn.cursor()
                    cur.execute("UPDATE orders SET status='Paid', utr=? WHERE order_id=?", (utr, order_id))
                    conn.commit()
            except:
                pass

            try:
                bot.send_message(chat_id,
                    f"🎉 <b>Premium Activated!</b> 🎉\n\n"
                    f"📦 Plan: <b>{plan['name']}</b>\n"
                    f"🆔 UTR: <code>{utr}</code>\n"
                    f"📅 Expires: <code>{expiry[:16] if expiry else 'N/A'}</code>\n\n"
                    f"Thank you! 🙏")
            except:
                pass

            try:
                bot.send_message(ADMIN_ID,
                    f"💰 <b>Payment Received!</b>\n\n"
                    f"👤 User: <code>{user_id}</code>\n"
                    f"📦 Plan: <b>{plan['name']}</b>\n"
                    f"🆔 UTR: <code>{utr}</code>")
            except:
                pass
            return

        if result:
            status = result.get("status", "").lower()
            if status in ["failed", "expired", "cancelled", "error"]:
                try:
                    bot.send_message(chat_id, f"❌ Payment {status}.")
                except:
                    pass
                return

    try:
        bot.send_message(chat_id,
            f"⏰ <b>Payment Not Detected</b>\n\n"
            f"🆔 Order ID: <code>{order_id}</code>\n\n"
            f"🔄 Try again — Tap 💎 Buy Premium")
    except:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("auto_check:"))
def auto_check_handler(call):
    order_id = call.data.split(":")[1]
    bot.answer_callback_query(call.id, "🔍 Checking...")
    result = verify_payment(order_id)
    success, info = is_payment_success(result)

    if success:
        cur = conn.cursor()
        cur.execute("SELECT user_id, plan_key FROM orders WHERE order_id=?", (order_id,))
        row = cur.fetchone()
        if row:
            user_id, plan_key = row[0], row[1]
            plan = PREMIUM_PLANS.get(plan_key)
            activate_premium(user_id, plan_key)
            expiry = get_premium_expiry(user_id)
            utr = info.get("utr", "N/A")
            with db_lock:
                cur2 = conn.cursor()
                cur2.execute("UPDATE orders SET status='Paid', utr=? WHERE order_id=?", (utr, order_id))
                conn.commit()
            bot.answer_callback_query(call.id, "✅ Verified!", show_alert=True)
            bot.send_message(call.message.chat.id,
                f"🎉 <b>Premium Activated!</b>\n\n"
                f"📦 Plan: <b>{plan['name']}</b>\n"
                f"🆔 UTR: <code>{utr}</code>")
    else:
        bot.answer_callback_query(call.id, "⏳ Not received yet.", show_alert=True)

@bot.message_handler(commands=['myplan'])
def my_plan_handler(message):
    user_id = message.from_user.id
    if is_premium(user_id):
        expiry = get_premium_expiry(user_id)
        plan_name = get_premium_plan_name(user_id) or "Premium"
        bot.send_message(message.chat.id,
            f"💎 <b>Premium Active</b>\n\n"
            f"📦 Plan: <b>{plan_name}</b>\n"
            f"⏰ Expires: <code>{expiry[:16] if expiry else 'N/A'}</code>")
    else:
        bot.send_message(message.chat.id, "💎 You are not Premium. Tap 💎 Buy Premium!")

# ==========================================
# 🎁 REFER & EARN
# ==========================================
@bot.message_handler(func=lambda m: m.text == "🎁 𝐑𝐞𝐟𝐞𝐫 & 𝐄𝐚𝐫𝐧" or m.text == "🎁 Refer & Earn")
def refer_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return

    user_id = message.from_user.id
    ref_count = get_referral_count(user_id)
    bonus = get_referral_bonus(user_id)
    ref_link = get_referral_link(user_id)

    if ref_count >= 10:
        next_milestone = "🎉 <b>MAX LEVEL REACHED!</b>"
    elif ref_count >= 5:
        next_milestone = f"📈 Next: <b>10 refs</b> → <b>+5 slots</b> (Need {10 - ref_count})"
    elif ref_count >= 3:
        next_milestone = f"📈 Next: <b>5 refs</b> → <b>+2 slots</b> (Need {5 - ref_count})"
    else:
        next_milestone = f"📈 Next: <b>3 refs</b> → <b>+1 slot</b> (Need {3 - ref_count})"

    text = (
        "✨━━━━━━━━━━━━━━━━━━━━✨\n"
        "   🎁 <b>𝐑𝐄𝐅𝐄𝐑 &amp; 𝐄𝐀𝐑𝐍</b> 🎁\n"
        "✨━━━━━━━━━━━━━━━━━━━━✨\n\n"
        f"🔗 <b>Your Link:</b>\n<code>{ref_link}</code>\n\n"
        f"📊 <b>Stats:</b>\n"
        f"• Referrals: <b>{ref_count}</b>\n"
        f"• Bonus: <b>+{bonus}</b>\n\n"
        "🎯 <b>Rewards:</b>\n"
        "• 3 Refs → +1 Slot\n"
        "• 5 Refs → +2 Slots\n"
        "• 10 Refs → +5 Slots\n\n"
        f"{next_milestone}"
    )

    share_url = f"https://t.me/share/url?url={ref_link}&text=🔥 Check out this hosting bot!"
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📤 𝐒𝐡𝐚𝐫𝐞 𝐋𝐢𝐧𝐤", url=share_url))
    kb.row(InlineKeyboardButton("🔄 𝐑𝐞𝐟𝐫𝐞𝐬𝐡", callback_data="refresh_ref"))
    bot.send_message(message.chat.id, text, reply_markup=kb, disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda call: call.data == "refresh_ref")
def refresh_referral_handler(call):
    user_id = call.from_user.id
    ref_count = get_referral_count(user_id)
    bonus = get_referral_bonus(user_id)
    bot.answer_callback_query(call.id, f"📊 Refs: {ref_count} | Bonus: +{bonus}", show_alert=True)

# ==========================================
# 📢 UPDATES CHANNEL
# ==========================================
@bot.message_handler(func=lambda m: m.text == "📢 𝐔𝐩𝐝𝐚𝐭𝐞𝐬 𝐂𝐡𝐚𝐧𝐧𝐞𝐥" or m.text == "📢 Updates Channel")
def updates_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("📢 𝐉𝐨𝐢𝐧 𝐔𝐩𝐝𝐚𝐭𝐞𝐬 𝐂𝐡𝐚𝐧𝐧𝐞𝐥", url=CHANNEL_LINK))
    bot.send_message(message.chat.id, "📢 <b>Updates Channel</b>\n\n👇 Tap:", reply_markup=kb)

# ==========================================
# 📞 CONTACT OWNER
# ==========================================
@bot.message_handler(func=lambda m: m.text == "📞 𝐂𝐨𝐧𝐭𝐚𝐜𝐭 𝐎𝐰𝐧𝐞𝐫" or m.text == "📞 Contact Owner")
def contact_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton("💬 𝐌𝐞𝐬𝐬𝐚𝐠𝐞 𝐎𝐰𝐧𝐞𝐫", url=OWNER_LINK))
    bot.send_message(message.chat.id,
        f"📞 <b>Contact Owner</b>\n\n👤 @{OWNER_USERNAME}",
        reply_markup=kb)

# ==========================================
# ⚡ BOT SPEED
# ==========================================
@bot.message_handler(func=lambda m: m.text == "⚡ 𝐁𝐨𝐭 𝐒𝐩𝐞𝐞𝐝" or m.text == "⚡ Bot Speed")
def speed_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    cpu, memory, processes_count = get_system_load()
    uptime_td = datetime.utcnow() - START_TIME
    days = uptime_td.days
    hours, remainder = divmod(uptime_td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    bot.send_message(message.chat.id,
        f"⚡ <b>𝐒𝐲𝐬𝐭𝐞𝐦 𝐒𝐭𝐚𝐭𝐮𝐬</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🖥 CPU: <b>{cpu:.1f}%</b>\n"
        f"💾 Memory: <b>{memory:.1f}%</b>\n"
        f"🚀 Running: <b>{processes_count}</b>\n"
        f"⏰ Uptime: <b>{days}d {hours}h {minutes}m</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━")

# ==========================================
# 📊 STATISTICS
# ==========================================
@bot.message_handler(func=lambda m: m.text == "📊 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬" or m.text == "📊 Statistics")
def stats_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM files")
    user_count = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM files")
    file_count = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM files WHERE status='Running'")
    running_count = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM files WHERE status='Pending'")
    pending_count = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM referrals")
    total_refs = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM premium_users")
    premium_count = cur.fetchone()[0] or 0
    cpu, memory, _ = get_system_load()
    bot.send_message(message.chat.id,
        f"📊 <b>𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Users: <b>{user_count}</b>\n"
        f"📁 Files: <b>{file_count}</b>\n"
        f"🟢 Running: <b>{running_count}</b>\n"
        f"⏳ Pending: <b>{pending_count}</b>\n"
        f"🎁 Referrals: <b>{total_refs}</b>\n"
        f"💎 Premium: <b>{premium_count}</b>\n"
        f"⚡ CPU: <b>{cpu:.1f}%</b>\n"
        f"💾 Memory: <b>{memory:.1f}%</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━")

# ==========================================
# 📁 MY FILES
# ==========================================
@bot.message_handler(func=lambda m: m.text == "📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬" or m.text == "📁 My Files")
def my_files_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    send_files_list(message.chat.id, message.from_user.id)

def send_files_list(chat_id, user_id):
    files = list_user_files(user_id)
    if not files:
        bot.send_message(chat_id, "📁 <b>Your Files</b>\n\n😕 No files uploaded yet.")
        return
    text = "📁 <b>Your Files</b>\n\n👇 Click to manage:"
    kb = InlineKeyboardMarkup()
    for file in files:
        file_id, filename, orig_name, uploaded, file_type, status, pid = file
        emoji = "🟢" if status == "Running" else "⏳" if status == "Pending" else "🔴"
        kb.add(InlineKeyboardButton(f"{emoji} {orig_name} ({file_type})", callback_data=f"manage:{file_id}"))
    bot.send_message(chat_id, text, reply_markup=kb)

# ==========================================
# 📤 UPLOAD FILE
# ==========================================
@bot.message_handler(func=lambda m: m.text == "📤 𝐔𝐩𝐥𝐨𝐚𝐝 𝐅𝐢𝐥𝐞" or m.text == "📤 Upload File")
def upload_handler(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "🔒 Join channel first.", reply_markup=force_join_kb())
        return
    bot.send_message(message.chat.id,
        "📤 <b>𝐔𝐩𝐥𝐨𝐚𝐝 𝐚 𝐅𝐢𝐥𝐞</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📄 Send Python (.py), JavaScript (.js), or archive (.zip/.tar.gz)\n\n"
        "⚠️ User files need Admin approval.\n"
        "👑 Admin files run directly.\n\n"
        "🔍 File auto-checked — errors will be reported!\n"
        "━━━━━━━━━━━━━━━━━━━━")

@bot.message_handler(content_types=['document'])
def document_handler(message):
    user = message.from_user
    user_id = user.id

    if not is_user_joined(user_id):
        bot.reply_to(message, "🔒 Join channel first.", reply_markup=force_join_kb())
        return

    is_prem = is_premium(user_id)

    if user_id != ADMIN_ID and not is_prem:
        user_files = list_user_files(user_id)
        effective_limit = get_effective_file_limit(user_id)
        if len(user_files) >= effective_limit:
            bot.reply_to(message, f"❌ File limit reached ({effective_limit}).\n🎁 Refer or 💎 Buy Premium!")
            return

    if message.document.file_size and message.document.file_size > MAX_UPLOAD_SIZE:
        bot.reply_to(message, f"❌ File too large (max 10 MB).")
        return

    try:
        file_info = bot.get_file(message.document.file_id)
        file_bytes = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.reply_to(message, f"❌ Download failed: {str(e)}")
        return

    original_filename = message.document.file_name or "unknown"
    file_type = get_file_type(original_filename)

    if file_type == "unknown" and not original_filename.lower().endswith(('.zip', '.tar', '.tar.gz', '.tgz')):
        bot.reply_to(
            message,
            f"❌ <b>THIS FILE CANNOT RUN!</b>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📁 <code>{html_lib.escape(original_filename)}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🚫 <b>Reason:</b> Unsupported format\n\n"
            f"✅ <b>Only these are allowed:</b>\n"
            f"• 🐍 <code>.py</code> — Python\n"
            f"• 📜 <code>.js</code> — JavaScript\n"
            f"• 📦 <code>.zip</code> — ZIP\n"
            f"• 📦 <code>.tar.gz</code> — Tar\n\n"
            f"💡 Send in a valid format.",
            parse_mode="HTML"
        )
        return

    user_dir = os.path.join(UPLOADS_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    safe_name = sanitize_filename(original_filename)
    safe_filename = f"{int(time.time())}_{safe_name}"
    file_path = os.path.join(user_dir, safe_filename)

    try:
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
    except Exception as e:
        bot.reply_to(message, f"❌ Save failed: {str(e)}")
        return

    final_path = file_path
    main_file_for_check = None

    if file_type in ["zip", "archive"]:
        bot.reply_to(message, "📦 Extracting archive...")
        extracted_dir = os.path.join(TEMP_DIR, f"extracted_{user_id}_{int(time.time())}")
        os.makedirs(extracted_dir, exist_ok=True)
        success, error = extract_archive(file_path, extracted_dir)
        if not success:
            bot.reply_to(message,
                f"❌ <b>Archive extraction failed!</b>\n\n<b>Reason:</b> {html_lib.escape(str(error))}",
                parse_mode="HTML")
            try:
                os.remove(file_path)
                shutil.rmtree(extracted_dir, ignore_errors=True)
            except:
                pass
            return

        main_file = find_main_file(extracted_dir)
        if not main_file:
            bot.reply_to(
                message,
                "❌ <b>THIS FILE CANNOT RUN!</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🚫 <b>Reason:</b> No <code>.py</code> or <code>.js</code> file found in archive\n\n"
                "💡 <b>Solution:</b>\n"
                "• Keep <code>main.py</code> / <code>bot.py</code> in archive\n"
                "• Or keep any one <code>.py</code>/<code>.js</code> file",
                parse_mode="HTML"
            )
            try:
                shutil.rmtree(extracted_dir, ignore_errors=True)
                os.remove(file_path)
            except:
                pass
            return

        final_path = extracted_dir
        main_file_for_check = main_file
        file_type = get_file_type(main_file)
        bot.reply_to(message,
            f"✅ Main file: <code>{os.path.basename(main_file)}</code>\n🔍 Checking...",
            parse_mode="HTML")
    else:
        main_file_for_check = file_path

    bot.send_chat_action(message.chat.id, 'typing')
    is_valid, err_type, err_msg, line_no = validate_file(main_file_for_check, file_type)

    if not is_valid:
        try:
            if os.path.isdir(final_path):
                shutil.rmtree(final_path, ignore_errors=True)
            else:
                os.remove(final_path)
        except:
            pass

        error_report = format_validation_error(err_type, err_msg, original_filename)
        bot.send_message(message.chat.id, error_report, parse_mode="HTML")

        try:
            bot.send_message(
                ADMIN_ID,
                f"⚠️ <b>User sent invalid file</b>\n\n"
                f"👤 {html_lib.escape(user.first_name or 'User')} (<code>{user_id}</code>)\n"
                f"📁 {html_lib.escape(original_filename)}\n"
                f"❌ Error: <b>{err_type}</b>\n"
                f"📍 Line: <b>{line_no or 'N/A'}</b>",
                parse_mode="HTML"
            )
        except:
            pass
        return

    if file_type == "python":
        missing_imports = check_imports_available(main_file_for_check, file_type)
        if missing_imports:
            bot.send_message(
                message.chat.id,
                f"⚠️ <b>Warning:</b> Missing modules:\n"
                f"<code>{', '.join(missing_imports)}</code>\n\n"
                f"💡 Will try auto-install on start.",
                parse_mode="HTML"
            )

    if is_valid:
        extra = ""
        if err_msg and err_type == "ok":
            extra = f"\n\n{err_msg}"

        bot.send_message(
            message.chat.id,
            f"✅ <b>File check PASSED!</b>\n\n"
            f"📁 {html_lib.escape(original_filename)}\n"
            f"🐍 Type: {file_type}{extra}",
            parse_mode="HTML"
        )

    if user_id == ADMIN_ID or is_prem:
        file_id = add_file_record(user_id, user.username, safe_filename, original_filename, final_path, file_type, status="Stopped")
        bot.reply_to(message, "👑 Direct start..." if user_id == ADMIN_ID else "💎 Premium — Direct start...")
        start_file_process(file_id, message.chat.id)
    else:
        file_id = add_file_record(user_id, user.username, safe_filename, original_filename, final_path, file_type, status="Pending")
        bot.reply_to(message, "⏳ Sent for Admin approval.")
        try:
            caption = (f"🔔 <b>New File Approval Request</b>\n\n"
                       f"👤 User: {html_lib.escape(user.first_name or 'User')}\n"
                       f"🆔 ID: <code>{user_id}</code>\n"
                       f"📁 File: <code>{html_lib.escape(original_filename)}</code>\n"
                       f"📊 Type: {file_type}\n"
                       f"✅ Validation: <b>PASSED</b>\n"
                       f"🆔 File ID: <code>{file_id}</code>")
            if os.path.isfile(final_path):
                with open(final_path, 'rb') as f:
                    bot.send_document(ADMIN_ID, f, caption=caption, reply_markup=admin_approval_kb(file_id), parse_mode="HTML")
            else:
                bot.send_message(ADMIN_ID, caption, reply_markup=admin_approval_kb(file_id), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Admin notify failed: {e}")

# ==========================================
# ▶️ START FILE PROCESS
# ==========================================
def start_file_process(file_id, chat_id):
    should_stop, reason = should_stop_due_to_load()
    if should_stop:
        bot.send_message(chat_id, f"⚠️ Cannot start: {reason}")
        return

    file_record = get_file_record(file_id)
    if not file_record:
        bot.send_message(chat_id, "❌ File not found")
        return
    file_path = file_record["path"]
    original_name = file_record["orig_name"]

    target_file = None
    working_dir = None
    if os.path.isdir(file_path):
        main_file = find_main_file(file_path)
        if not main_file:
            bot.send_message(chat_id, "❌ No main file found")
            return
        target_file = main_file
        working_dir = os.path.dirname(main_file)
    else:
        if not os.path.exists(file_path):
            bot.send_message(chat_id, f"❌ File not found")
            return
        target_file = file_path
        working_dir = os.path.dirname(file_path)

    ext = os.path.splitext(target_file)[1].lower()

    if ext == ".py":
        requirements_path = os.path.join(working_dir, "requirements.txt")
        if os.path.exists(requirements_path):
            bot.send_message(chat_id, "📦 Installing requirements.txt...")
            success, message = install_requirements_from_file(requirements_path, chat_id, original_name)
            bot.send_message(chat_id, f"✅ {message}" if success else f"⚠️ {message}")
        bot.send_message(chat_id, "🔍 Checking imports...")
        imports = extract_imports(target_file)
        if imports:
            success, message = install_missing_imports(imports, chat_id, original_name)
            bot.send_message(chat_id, f"📦 {message}")

    if ext == ".py":
        cmd = [sys.executable, target_file]
    elif ext == ".js":
        cmd = ["node", target_file]
    else:
        bot.send_message(chat_id, f"❌ Unsupported: {ext}")
        return

    log_filename = f"file_{file_id}_{int(time.time())}.log"
    log_path = os.path.join(LOGS_DIR, log_filename)

    try:
        log_file_handle = open(log_path, 'w')
        process = subprocess.Popen(cmd, stdout=log_file_handle, stderr=subprocess.STDOUT, cwd=working_dir, text=True)
        run_id = record_run_start(file_id, process.pid, log_path)
        update_file_status(file_id, process.pid, "Running")
        with proc_lock:
            processes[file_id] = {'process': process, 'run_id': run_id, 'log_path': log_path,
                                  'started_at': datetime.utcnow().isoformat(),
                                  'log_file_handle': log_file_handle}
        bot.send_message(chat_id,
            f"✅ <b>{html_lib.escape(original_name)}</b> started!\n"
            f"📝 PID: <code>{process.pid}</code>\n"
            f"📁 Log: <code>{log_filename}</code>")

        def monitor_process():
            try:
                exit_code = process.wait()
            except Exception:
                exit_code = -1
            finally:
                try:
                    log_file_handle.close()
                except:
                    pass

                update_file_status(file_id, None, "Stopped")
                record_run_finish(run_id, exit_code)
                with proc_lock:
                    processes.pop(file_id, None)

                if exit_code != 0:
                    report = format_crash_report(original_name, exit_code, log_path)
                    try:
                        bot.send_message(chat_id, report, parse_mode="HTML")
                    except Exception as se:
                        logger.error(f"Error report failed: {se}")
                        try:
                            bot.send_message(chat_id, f"❌ {original_name} crashed. Exit: {exit_code}")
                        except:
                            pass

                    try:
                        bot.send_message(ADMIN_ID,
                            f"⚠️ <b>File Crash</b>\n\n"
                            f"📁 {html_lib.escape(original_name)}\n"
                            f"📛 Exit: <code>{exit_code}</code>\n"
                            f"👤 Chat: <code>{chat_id}</code>",
                            parse_mode="HTML")
                    except:
                        pass
                else:
                    try:
                        bot.send_message(chat_id,
                            f"✅ <b>{html_lib.escape(original_name)}</b> completed successfully.",
                            parse_mode="HTML")
                    except:
                        pass

        threading.Thread(target=monitor_process, daemon=True).start()
    except Exception as e:
        bot.send_message(chat_id, f"❌ Failed to start: {str(e)}")

def stop_file_process(file_id):
    with proc_lock:
        if file_id in processes:
            process = processes[file_id]['process']
            log_handle = processes[file_id].get('log_file_handle')
            try:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            except Exception as e:
                logger.error(f"Error stopping {file_id}: {e}")
            try:
                if log_handle:
                    log_handle.close()
            except:
                pass
            processes.pop(file_id, None)
    update_file_status(file_id, None, "Stopped")

def get_file_logs(file_id, lines=50):
    try:
        with proc_lock:
            if file_id in processes:
                log_path = processes[file_id]['log_path']
                if os.path.exists(log_path):
                    with open(log_path, 'r') as f:
                        content = f.readlines()
                    return ''.join(content[-lines:]) if content else "😕 No logs yet"
        cur = conn.cursor()
        cur.execute("SELECT log_path FROM runs WHERE file_id=? ORDER BY started_at DESC LIMIT 1", (file_id,))
        row = cur.fetchone()
        if row and row[0] and os.path.exists(row[0]):
            with open(row[0], 'r') as f:
                content = f.readlines()
            return ''.join(content[-lines:]) if content else "😕 No logs found"
        return "😕 No log file found"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ==========================================
# 🎛️ CALLBACK HANDLER
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    if data == "back_to_files":
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        send_files_list(chat_id, user_id)
        return

    if data == "refresh_ref":
        ref_count = get_referral_count(user_id)
        bonus = get_referral_bonus(user_id)
        bot.answer_callback_query(call.id, f"📊 Refs: {ref_count} | Bonus: +{bonus}", show_alert=True)
        return

    try:
        if data.startswith("approve:"):
            file_id = int(data.split(":")[1])
            bot.answer_callback_query(call.id, "Approved ✅")
            file_record = get_file_record(file_id)
            if file_record:
                try:
                    bot.send_message(file_record["user_id"],
                        f"✅ Your file <b>{html_lib.escape(file_record['orig_name'])}</b> approved!\n🚀 Starting...")
                except:
                    pass
                start_file_process(file_id, file_record["user_id"])
            try:
                bot.edit_message_caption(caption=f"✅ File ID {file_id} Approved.",
                                         chat_id=chat_id, message_id=call.message.message_id)
            except:
                try:
                    bot.edit_message_text(f"✅ Approved.", chat_id, call.message.message_id)
                except:
                    pass

        elif data.startswith("reject:"):
            file_id = int(data.split(":")[1])
            bot.answer_callback_query(call.id, "Rejected ❌")
            file_record = get_file_record(file_id)
            if file_record:
                try:
                    if os.path.isdir(file_record["path"]):
                        shutil.rmtree(file_record["path"], ignore_errors=True)
                    elif os.path.exists(file_record["path"]):
                        os.remove(file_record["path"])
                except:
                    pass
                try:
                    bot.send_message(file_record["user_id"],
                        f"❌ Your file was rejected.")
                except:
                    pass
                remove_file_record(file_id)
            try:
                bot.edit_message_caption(caption=f"❌ File ID {file_id} Rejected.",
                                         chat_id=chat_id, message_id=call.message.message_id)
            except:
                try:
                    bot.edit_message_text(f"❌ Rejected.", chat_id, call.message.message_id)
                except:
                    pass

        elif data.startswith("manage:"):
            file_id = int(data.split(":")[1])
            show_file_management(chat_id, file_id, user_id, call.message.message_id)

        elif data.startswith("start:"):
            file_id = int(data.split(":")[1])
            bot.answer_callback_query(call.id, "Starting... 🚀")
            start_file_process(file_id, chat_id)
            time.sleep(1)
            show_file_management(chat_id, file_id, user_id, call.message.message_id)

        elif data.startswith("stop:"):
            file_id = int(data.split(":")[1])
            bot.answer_callback_query(call.id, "Stopping... ⏹")
            stop_file_process(file_id)
            bot.send_message(chat_id, "⏹ Stopped.")
            time.sleep(1)
            show_file_management(chat_id, file_id, user_id, call.message.message_id)

        elif data.startswith("restart:"):
            file_id = int(data.split(":")[1])
            bot.answer_callback_query(call.id, "Restarting... 🔁")
            stop_file_process(file_id)
            time.sleep(2)
            start_file_process(file_id, chat_id)
            time.sleep(1)
            show_file_management(chat_id, file_id, user_id, call.message.message_id)

        elif data.startswith("delete:"):
            file_id = int(data.split(":")[1])
            bot.answer_callback_query(call.id, "Deleting... 🗑")
            file_record = get_file_record(file_id)
            if file_record:
                stop_file_process(file_id)
                try:
                    if os.path.isdir(file_record["path"]):
                        shutil.rmtree(file_record["path"], ignore_errors=True)
                    elif os.path.exists(file_record["path"]):
                        os.remove(file_record["path"])
                except:
                    pass
                remove_file_record(file_id)
            bot.send_message(chat_id, "🗑 Deleted.")
            send_files_list(chat_id, user_id)

        elif data.startswith("logs:"):
            file_id = int(data.split(":")[1])
            bot.answer_callback_query(call.id, "Fetching logs... 📄")
            logs = get_file_logs(file_id)
            file_record = get_file_record(file_id)
            file_name = file_record["orig_name"] if file_record else "Unknown"
            if len(logs) > 4000:
                logs = "... (truncated) ...\n" + logs[-4000:]
            bot.send_message(chat_id, f"📄 <b>Logs — {html_lib.escape(file_name)}</b>\n\n<pre>{html_lib.escape(logs)}</pre>")

    except Exception as e:
        bot.answer_callback_query(call.id, "Error ❌")
        logger.error(f"Callback error: {e}")

def show_file_management(chat_id, file_id, user_id, message_id=None):
    file_record = get_file_record(file_id)
    if not file_record:
        bot.send_message(chat_id, "❌ File not found")
        return
    if file_record["user_id"] != user_id and user_id != ADMIN_ID:
        bot.send_message(chat_id, "❌ Access denied")
        return
    is_running = False
    with proc_lock:
        is_running = file_id in processes
    if is_running:
        status_text = "🟢 Running"
    elif file_record['status'] == "Pending":
        status_text = "⏳ Pending Approval"
    else:
        status_text = "🔴 Stopped"
    pid_text = f"\n📝 PID: {file_record['pid']}" if file_record['pid'] else ""
    text = (f"⚙️ <b>File Management</b>\n\n"
            f"📁 File: {html_lib.escape(file_record['orig_name'])}\n"
            f"📊 Type: {file_record['file_type']}\n"
            f"📈 Status: {status_text}{pid_text}\n"
            f"⏰ Uploaded: {file_record['uploaded_at'][:16]}")
    kb = file_actions_kb(file_id, is_running)
    if message_id:
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        except:
            bot.send_message(chat_id, text, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

# ==========================================
# 🚀 START BOT
# ==========================================
def start_bot():
    logger.info("🚀 Starting 24x7 AJAY HOSTING BOT — ROYAL PREMIUM EDITION...")

    threading.Thread(target=auto_memory_manager, daemon=True).start()
    threading.Thread(target=auto_cleaner, daemon=True).start()
    threading.Thread(target=garbage_collector, daemon=True).start()

    logger.info("🧠 Auto Memory Manager is running...")
    logger.info("🗑 Auto Cleaner is running...")
    logger.info("♻️ Garbage Collector is running...")

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=50)
        except KeyboardInterrupt:
            STOP_EVENT.set()
            break
        except SystemExit:
            STOP_EVENT.set()
            break
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(5)
        if STOP_EVENT.is_set():
            break

if __name__ == "__main__":
    start_bot()