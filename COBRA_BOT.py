# COBRA_BOT.py
# ====================================================
# بخش ۱: ایمپورت‌ها + تنظیمات + Flask App
# ====================================================

import requests
import json
import time
import random
import re
import os
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# ====== تنظیمات اصلی ======
TOKEN = "BJAEIG0EYJOJRBKVMUMYAXEIBHGOFZXIDXFUMSTGCWIQPTKITUQQVRERFWYKBQVA"
BASE_URL = f"https://botapi.rubika.ir/v3/{TOKEN}"

INITIAL_BALANCE = 1000000
CURRENCY = "کبرا کوین"
GEM_CURRENCY = "کبرا جم"
GEM_PRICE = 10000000
last_processed = {}

BALANCE_FILE = "balances.json"
STARTUP_TIME = time.time()

# ====== کلمات ممنوعه ======
FORBIDDEN_WORDS = [
    "فحش1",
    "فحش2",
    "فحش3",
]
WARNING_LIMIT = 3
BAN_DURATION = 86400

# ====== سیستم مالکیت ======
OWNER_PASSWORD = "MaLeKiAt_COBRA_BoT"
OWNER_FILE = "owner.json"

# ====== وضعیت‌های پنل ======
PANEL_STATES = {}
PANEL_OPEN = {}

# ====== Flask App ======
app = Flask(__name__)

# ====================================================
# کدهای هدیه
# ====================================================

GIFT_CODES = {
    "UPDATE_GIFT_CODE": {
        "reward": 2000000,
        "expire_date": "2026-07-11 23:59:59",
        "used_by": []
    },
    "HAMINIOORI": {
        "reward": 3000000,
        "expire_date": "2026-07-13 23:59:59",
        "used_by": []
    }
}

# ====================================================
# توابع مالکیت
# ====================================================

def load_owner():
    if os.path.exists(OWNER_FILE):
        try:
            with open(OWNER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("owner_id"), data.get("owner_chat_id")
        except:
            return None, None
    return None, None

def save_owner(owner_id, chat_id):
    with open(OWNER_FILE, 'w', encoding='utf-8') as f:
        json.dump({"owner_id": owner_id, "owner_chat_id": chat_id}, f)

def clear_owner():
    if os.path.exists(OWNER_FILE):
        os.remove(OWNER_FILE)

def is_owner(sender_id):
    owner_id, _ = load_owner()
    return owner_id == sender_id

# ====================================================
# توابع پایه
# ====================================================

def generate_short_id():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=7))

def generate_card_number():
    card = "5"
    for _ in range(15):
        card += str(random.randint(0, 9))
    return card

def generate_gem_card_number():
    card = "6"
    for _ in range(15):
        card += str(random.randint(0, 9))
    return card

def format_number(num):
    if num == float('inf') or num == 9999999999999999:
        return "∞"
    try:
        return f"{int(num):,}"
    except:
        return str(num)

# ====================================================
# توابع ذخیره و بارگذاری
# ====================================================

def load_balances():
    if os.path.exists(BALANCE_FILE):
        try:
            with open(BALANCE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            converted = False
            for key, value in list(data.items()):
                if isinstance(value, (int, float)):
                    data[key] = {
                        "balance": int(value),
                        "nickname": None,
                        "games_played": 0,
                        "card_number": generate_card_number(),
                        "gem_card_number": generate_gem_card_number(),
                        "short_id": generate_short_id(),
                        "registered": False,
                        "last_spin": 0,
                        "gems": 0,
                        "show_in_coin_leaderboard": True,
                        "show_in_gem_leaderboard": True,
                        "used_gift_codes": [],
                        "banned": False,
                        "ban_reason": None,
                        "ban_until": None,
                        "original_balance": None,
                        "original_gems": None,
                        "is_owner": False,
                        "warnings": 0,
                        "warning_reason": None,
                        "job": None,
                        "phones": [],
                        "laptops": [],
                        "cars": [],
                        "sims": [],
                        "friends": [],
                        "friend_requests": [],
                        "last_salary": 0
                    }
                    converted = True
                elif isinstance(value, dict) and "phones" not in value:
                    value["phones"] = []
                    value["laptops"] = []
                    value["cars"] = []
                    value["sims"] = []
                    converted = True
                elif isinstance(value, dict) and "friends" not in value:
                    value["friends"] = []
                    value["friend_requests"] = []
                    value["last_salary"] = 0
                    converted = True
            if converted:
                save_balances(data)
                print("🔄 فایل موجودی به‌روزرسانی شد.")
            return data
        except Exception as e:
            print(f"❌ خطا در خواندن فایل: {e}")
            return {}
    return {}

def save_balances(balances):
    try:
        with open(BALANCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(balances, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ خطا در ذخیره فایل: {e}")
        return False

def get_startup_time():
    return STARTUP_TIME

def get_user_data(chat_id, user_id, balances):
    key = f"{chat_id}_{user_id}"
    if key not in balances:
        balances[key] = {
            "balance": INITIAL_BALANCE,
            "nickname": None,
            "games_played": 0,
            "card_number": generate_card_number(),
            "gem_card_number": generate_gem_card_number(),
            "short_id": generate_short_id(),
            "registered": False,
            "last_spin": 0,
            "gems": 0,
            "show_in_coin_leaderboard": True,
            "show_in_gem_leaderboard": True,
            "used_gift_codes": [],
            "banned": False,
            "ban_reason": None,
            "ban_until": None,
            "original_balance": None,
            "original_gems": None,
            "is_owner": False,
            "warnings": 0,
            "warning_reason": None,
            "job": None,
            "phones": [],
            "laptops": [],
            "cars": [],
            "sims": [],
            "friends": [],
            "friend_requests": [],
            "last_salary": 0
        }
        save_balances(balances)
    return balances[key]

def update_user_data(chat_id, user_id, balances, field, value):
    user_data = get_user_data(chat_id, user_id, balances)
    user_data[field] = value
    save_balances(balances)
    return user_data
    # ====================================================
# بخش ۲: لیست‌ها
# ====================================================

XIAOMI_PHONES = {
    "redmi_9a": {"name": "Redmi 9A", "storage": "8GB", "price": 6500000},
    "redmi_9c": {"name": "Redmi 9C", "storage": "16GB", "price": 6850000},
    "redmi_10a": {"name": "Redmi 10A", "storage": "16GB", "price": 7050000},
    "redmi_12c": {"name": "Redmi 12C", "storage": "16GB", "price": 23500000},
    "redmi_13c": {"name": "Redmi 13C", "storage": "16GB", "price": 25500000},
    "redmi_note_12": {"name": "Redmi Note 12", "storage": "16GB", "price": 48400000},
    "redmi_note_13": {"name": "Redmi Note 13", "storage": "32GB", "price": 55000000},
    "redmi_note_14": {"name": "Redmi Note 14", "storage": "32GB", "price": 65600000},
    "poco_x6": {"name": "Poco X6", "storage": "64GB", "price": 85000000},
    "xiaomi_14_ultra": {"name": "Xiaomi 14 Ultra", "storage": "64GB", "price": 293000000},
}

SAMSUNG_PHONES = {
    "a04e": {"name": "Galaxy A04e", "storage": "16GB", "price": 13000000},
    "a04": {"name": "Galaxy A04", "storage": "32GB", "price": 13700000},
    "a05": {"name": "Galaxy A05", "storage": "32GB", "price": 14100000},
    "a06": {"name": "Galaxy A06", "storage": "32GB", "price": 47000000},
    "a06_5g": {"name": "Galaxy A06 5G", "storage": "32GB", "price": 51000000},
    "a07": {"name": "Galaxy A07", "storage": "32GB", "price": 96800000},
    "a16": {"name": "Galaxy A16", "storage": "64GB", "price": 110000000},
    "a17": {"name": "Galaxy A17", "storage": "64GB", "price": 131200000},
    "a26": {"name": "Galaxy A26", "storage": "128GB", "price": 170000000},
    "s25_ultra": {"name": "Galaxy S25 Ultra", "storage": "128GB", "price": 586000000},
}

IPHONE_PHONES = {
    "iphone_11": {"name": "iPhone 11", "storage": "32GB", "price": 26000000},
    "iphone_12": {"name": "iPhone 12", "storage": "64GB", "price": 27400000},
    "iphone_13": {"name": "iPhone 13", "storage": "64GB", "price": 28200000},
    "iphone_14": {"name": "iPhone 14", "storage": "64GB", "price": 94000000},
    "iphone_15": {"name": "iPhone 15", "storage": "64GB", "price": 102000000},
    "iphone_16": {"name": "iPhone 16", "storage": "64GB", "price": 193600000},
    "iphone_16_pro": {"name": "iPhone 16 Pro", "storage": "128GB", "price": 220000000},
    "iphone_17": {"name": "iPhone 17", "storage": "128GB", "price": 262400000},
    "iphone_17_pro": {"name": "iPhone 17 Pro", "storage": "256GB", "price": 340000000},
    "iphone_17_pro_max": {"name": "iPhone 17 Pro Max", "storage": "256GB", "price": 1172000000},
}

ASUS_LAPTOPS = {
    "asus_1": {"name": "Vivobook E410", "ram": "2GB", "ssd": "64GB", "price": 90000000},
    "asus_2": {"name": "Vivobook 14 X1404VA", "ram": "4GB", "ssd": "128GB", "price": 120000000},
    "asus_3": {"name": "Vivobook 15 X1504VA", "ram": "4GB", "ssd": "256GB", "price": 180000000},
    "asus_4": {"name": "Vivobook 16 M1605YA", "ram": "8GB", "ssd": "512GB", "price": 220000000},
    "asus_5": {"name": "Vivobook S 14 Flip", "ram": "8GB", "ssd": "1TB", "price": 300000000},
    "asus_6": {"name": "Zenbook 14 OLED", "ram": "16GB", "ssd": "2TB", "price": 360000000},
    "asus_7": {"name": "TUF Gaming A15", "ram": "16GB", "ssd": "4TB", "price": 500000000},
    "asus_8": {"name": "TUF Gaming F16", "ram": "32GB", "ssd": "64GB", "price": 640000000},
    "asus_9": {"name": "ROG Strix G18", "ram": "32GB", "ssd": "128GB", "price": 1250000000},
    "asus_10": {"name": "ROG Zephyrus G16", "ram": "64GB", "ssd": "256GB", "price": 1700000000},
}

HP_LAPTOPS = {
    "hp_1": {"name": "HP 250 G9", "ram": "4GB", "ssd": "128GB", "price": 106000000},
    "hp_2": {"name": "HP 15-fd0362", "ram": "4GB", "ssd": "256GB", "price": 240000000},
    "hp_3": {"name": "HP 15-fd0174", "ram": "8GB", "ssd": "512GB", "price": 300000000},
    "hp_4": {"name": "HP 15-fd1310", "ram": "8GB", "ssd": "1TB", "price": 376000000},
    "hp_5": {"name": "HP Victus 15", "ram": "16GB", "ssd": "2TB", "price": 440000000},
    "hp_6": {"name": "HP Omen 16", "ram": "16GB", "ssd": "4TB", "price": 560000000},
    "hp_7": {"name": "HP Omen 16 (RTX 5060)", "ram": "32GB", "ssd": "64GB", "price": 808000000},
    "hp_8": {"name": "HP Omen Slim 16", "ram": "32GB", "ssd": "128GB", "price": 1000000000},
    "hp_9": {"name": "HP ZBook Studio", "ram": "64GB", "ssd": "256GB", "price": 1400000000},
    "hp_10": {"name": "HP ZBook Fury", "ram": "64GB", "ssd": "512GB", "price": 1900000000},
}

MACBOOK_LAPTOPS = {
    "mac_1": {"name": "MacBook Neo", "ram": "8GB", "ssd": "512GB", "price": 280000000},
    "mac_2": {"name": "MacBook Air M5", "ram": "8GB", "ssd": "1TB", "price": 408000000},
    "mac_3": {"name": "MacBook Air M5", "ram": "12GB", "ssd": "2TB", "price": 482000000},
    "mac_4": {"name": "MacBook Air M5", "ram": "12GB", "ssd": "4TB", "price": 564000000},
    "mac_5": {"name": "MacBook Air 2026", "ram": "16GB", "ssd": "64GB", "price": 714000000},
    "mac_6": {"name": "MacBook Pro M5", "ram": "16GB", "ssd": "128GB", "price": 900000000},
    "mac_7": {"name": "MacBook Pro M5 Max", "ram": "24GB", "ssd": "256GB", "price": 1848000000},
    "mac_8": {"name": "MacBook Pro 16 M5 Max", "ram": "32GB", "ssd": "512GB", "price": 2200000000},
    "mac_9": {"name": "MacBook Pro 16", "ram": "32GB", "ssd": "1TB", "price": 3000000000},
    "mac_10": {"name": "MacBook Pro 16 Ultra", "ram": "64GB", "ssd": "2TB", "price": 4000000000},
}

SAIPA_CARS = {
    "pride": {"name": "پراید", "speed": 160, "price": 250000000},
    "tiba": {"name": "تیبا", "speed": 180, "price": 500000000},
    "tiba2": {"name": "تیبا ۲", "speed": 190, "price": 750000000},
    "saina": {"name": "ساینا", "speed": 200, "price": 1000000000},
    "quick": {"name": "کوییک", "speed": 210, "price": 1500000000},
    "shahin": {"name": "شاهین", "speed": 220, "price": 2000000000},
    "shahin_auto": {"name": "شاهین اتوماتیک", "speed": 230, "price": 2500000000},
    "aria": {"name": "آریا", "speed": 240, "price": 3000000000},
    "sahand": {"name": "سهند", "speed": 250, "price": 3500000000},
    "atlas": {"name": "اطلس", "speed": 260, "price": 4000000000},
}

IRANKHODRO_CARS = {
    "peykan": {"name": "پیکان", "speed": 140, "price": 350000000},
    "peugeot_405": {"name": "پژو 405", "speed": 180, "price": 750000000},
    "samand": {"name": "سمند", "speed": 190, "price": 1250000000},
    "peugeot_pars": {"name": "پژو پارس", "speed": 200, "price": 1800000000},
    "dena": {"name": "دنا", "speed": 210, "price": 2500000000},
    "dena_plus": {"name": "دنا پلاس", "speed": 220, "price": 3200000000},
    "rana_plus": {"name": "رانا پلاس", "speed": 230, "price": 4000000000},
    "tara": {"name": "تارا", "speed": 240, "price": 5000000000},
    "tara_auto": {"name": "تارا اتوماتیک", "speed": 250, "price": 6000000000},
    "haima_s7": {"name": "هایما S7", "speed": 260, "price": 7000000000},
}

TESLA_CARS = {
    "model_3": {"name": "Model 3", "speed": 250, "price": 10000000000},
    "model_y": {"name": "Model Y", "speed": 260, "price": 15000000000},
    "model_s": {"name": "Model S", "speed": 270, "price": 20000000000},
    "model_x": {"name": "Model X", "speed": 280, "price": 25000000000},
    "cybertruck": {"name": "Cybertruck", "speed": 290, "price": 30000000000},
    "roadster": {"name": "Roadster", "speed": 300, "price": 40000000000},
    "model_s_plaid": {"name": "Model S Plaid", "speed": 320, "price": 50000000000},
    "model_x_plaid": {"name": "Model X Plaid", "speed": 330, "price": 60000000000},
    "cybertruck_beast": {"name": "Cybertruck Beast", "speed": 340, "price": 75000000000},
    "tesla_semi": {"name": "Tesla Semi", "speed": 350, "price": 90000000000},
}

LAMBORGHINI_CARS = {
    "huracan": {"name": "Huracan", "speed": 300, "price": 22000000000},
    "huracan_evo": {"name": "Huracan EVO", "speed": 310, "price": 32000000000},
    "huracan_sto": {"name": "Huracan STO", "speed": 320, "price": 42000000000},
    "aventador": {"name": "Aventador", "speed": 330, "price": 52000000000},
    "aventador_svj": {"name": "Aventador SVJ", "speed": 340, "price": 62000000000},
    "revuelto": {"name": "Revuelto", "speed": 350, "price": 72000000000},
    "urus": {"name": "Urus", "speed": 360, "price": 82000000000},
    "urus_performante": {"name": "Urus Performante", "speed": 370, "price": 87000000000},
    "countach": {"name": "Countach", "speed": 380, "price": 92000000000},
    "sian": {"name": "Sian", "speed": 400, "price": 97000000000},
}

BUGATTI_CARS = {
    "veyron": {"name": "Veyron", "speed": 400, "price": 45000000000},
    "veyron_ss": {"name": "Veyron Super Sport", "speed": 410, "price": 55000000000},
    "chiron": {"name": "Chiron", "speed": 420, "price": 65000000000},
    "chiron_sport": {"name": "Chiron Sport", "speed": 430, "price": 70000000000},
    "chiron_pur_sport": {"name": "Chiron Pur Sport", "speed": 440, "price": 75000000000},
    "chiron_ss": {"name": "Chiron Super Sport", "speed": 450, "price": 80000000000},
    "divo": {"name": "Divo", "speed": 460, "price": 85000000000},
    "centodieci": {"name": "Centodieci", "speed": 470, "price": 88000000000},
    "la_voiture_noire": {"name": "La Voiture Noire", "speed": 480, "price": 93000000000},
    "bolide": {"name": "Bolide", "speed": 500, "price": 98000000000},
}

JOBS = {
    "دستفروش": {"emoji": "🛒", "price": 1000000, "salary": 250000, "phone": False, "laptop": False, "speed_needed": False},
    "کارگر ساده ساختمانی": {"emoji": "🧱", "price": 2500000, "salary": 500000, "phone": False, "laptop": False, "speed_needed": False},
    "نگهبان": {"emoji": "🚧", "price": 5000000, "salary": 1000000, "phone": True, "laptop": False, "speed_needed": False},
    "راننده اسنپ": {"emoji": "🚗", "price": 10000000, "salary": 2000000, "phone": True, "laptop": False, "speed_needed": True},
    "فروشنده مغازه": {"emoji": "🏪", "price": 20000000, "salary": 3500000, "phone": True, "laptop": False, "speed_needed": False},
    "منشی": {"emoji": "📞", "price": 40000000, "salary": 6000000, "phone": True, "laptop": True, "speed_needed": False},
    "آرایشگر": {"emoji": "✂️", "price": 70000000, "salary": 10000000, "phone": True, "laptop": False, "speed_needed": False},
    "راننده تاکسی": {"emoji": "🚕", "price": 100000000, "salary": 15000000, "phone": True, "laptop": False, "speed_needed": True},
    "آشپز": {"emoji": "👨‍🍳", "price": 150000000, "salary": 25000000, "phone": True, "laptop": False, "speed_needed": False},
    "عکاس": {"emoji": "📸", "price": 250000000, "salary": 40000000, "phone": True, "laptop": True, "speed_needed": True},
    "معلم": {"emoji": "📚", "price": 400000000, "salary": 60000000, "phone": True, "laptop": True, "speed_needed": False},
    "پرستار": {"emoji": "💉", "price": 600000000, "salary": 90000000, "phone": True, "laptop": False, "speed_needed": True},
    "یوتیوبر": {"emoji": "🎥", "price": None, "salary": None, "phone": True, "laptop": True, "speed_needed": False},
    "برنامه‌نویس": {"emoji": "💻", "price": 1000000000, "salary": 150000000, "phone": True, "laptop": True, "speed_needed": False},
    "وکیل": {"emoji": "⚖️", "price": 1500000000, "salary": 250000000, "phone": True, "laptop": True, "speed_needed": True},
    "پزشک": {"emoji": "🩺", "price": 2500000000, "salary": 400000000, "phone": True, "laptop": True, "speed_needed": True},
}

SIM_CARDS = {
    "rightel": {
        "name": "رایتل",
        "emoji": "📶",
        "price": 500000,
        "value": 1,
        "packages": {
            "1gb": {"size": "1GB", "price": 50000},
            "2gb": {"size": "2GB", "price": 90000},
            "4gb": {"size": "4GB", "price": 160000},
            "5gb": {"size": "5GB", "price": 190000},
            "7gb": {"size": "7GB", "price": 250000},
        }
    },
    "mci": {
        "name": "همراه اول",
        "emoji": "📡",
        "price": 1000000,
        "value": 2,
        "packages": {
            "1gb": {"size": "1GB", "price": 100000},
            "2gb": {"size": "2GB", "price": 180000},
            "4gb": {"size": "4GB", "price": 320000},
            "5gb": {"size": "5GB", "price": 380000},
            "7gb": {"size": "7GB", "price": 500000},
        }
    },
    "irancell": {
        "name": "ایرانسل",
        "emoji": "📱",
        "price": 2000000,
        "value": 3,
        "packages": {
            "1gb": {"size": "1GB", "price": 150000},
            "2gb": {"size": "2GB", "price": 270000},
            "4gb": {"size": "4GB", "price": 480000},
            "5gb": {"size": "5GB", "price": 570000},
            "7gb": {"size": "7GB", "price": 750000},
        }
    },
}

PHONE_MULTIPLIERS = {"xiaomi": 1, "samsung": 2, "iphone": 4}
LAPTOP_MULTIPLIERS = {"asus": 1, "hp": 2, "macbook": 4}
CAR_MULTIPLIERS = {"saipa": 1, "irankhodro": 2, "tesla": 4, "lamborghini": 8, "bugatti": 16}
SIM_MULTIPLIERS = {"rightel": 0, "mci": 1, "irancell": 2}
# ====================================================
# بخش ۳: توابع محاسبه + ارسال پیام
# ====================================================

def send_message(chat_id, text, reply_to_message_id=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ خطا: {e}")
        return False

def calculate_user_salary(user_data):
    if not user_data.get("job"):
        return None
    job_key = user_data.get("job")
    job = JOBS.get(job_key)
    if not job:
        return None
    base_salary = job.get("salary", 0)
    if base_salary is None:
        return None
    salary = base_salary
    
    phones = user_data.get("phones", [])
    if phones:
        best_price = 0
        for phone in phones:
            brand = phone.get("brand")
            model = phone.get("model")
            price = 0
            if brand == "شیامی":
                for k, p in XIAOMI_PHONES.items():
                    if p["name"] == model:
                        price = p["price"]
                        break
            elif brand == "سامسونگ":
                for k, p in SAMSUNG_PHONES.items():
                    if p["name"] == model:
                        price = p["price"]
                        break
            elif brand == "آیفون":
                for k, p in IPHONE_PHONES.items():
                    if p["name"] == model:
                        price = p["price"]
                        break
            if price > best_price:
                best_price = price
        if best_price > 0:
            salary += best_price * 0.01
    
    laptops = user_data.get("laptops", [])
    if laptops:
        best_price = 0
        for laptop in laptops:
            brand = laptop.get("brand")
            model = laptop.get("model")
            price = 0
            if brand == "ایسوس":
                for k, l in ASUS_LAPTOPS.items():
                    if l["name"] == model:
                        price = l["price"]
                        break
            elif brand == "اچ پی":
                for k, l in HP_LAPTOPS.items():
                    if l["name"] == model:
                        price = l["price"]
                        break
            elif brand == "مک بوک":
                for k, l in MACBOOK_LAPTOPS.items():
                    if l["name"] == model:
                        price = l["price"]
                        break
            if price > best_price:
                best_price = price
        if best_price > 0:
            salary += best_price * 0.01
    
    cars = user_data.get("cars", [])
    if cars:
        best_speed = 0
        for car in cars:
            brand = car.get("brand")
            model = car.get("model")
            speed = 0
            if brand == "سایپا":
                for k, c in SAIPA_CARS.items():
                    if c["name"] == model:
                        speed = c["speed"]
                        break
            elif brand == "ایران خودرو":
                for k, c in IRANKHODRO_CARS.items():
                    if c["name"] == model:
                        speed = c["speed"]
                        break
            elif brand == "تسلا":
                for k, c in TESLA_CARS.items():
                    if c["name"] == model:
                        speed = c["speed"]
                        break
            elif brand == "لامبورگینی":
                for k, c in LAMBORGHINI_CARS.items():
                    if c["name"] == model:
                        speed = c["speed"]
                        break
            elif brand == "بوگاتی":
                for k, c in BUGATTI_CARS.items():
                    if c["name"] == model:
                        speed = c["speed"]
                        break
            if speed > best_speed:
                best_speed = speed
        if best_speed > 0:
            salary += base_salary * 0.05 * (best_speed / 100)
    
    if job_key == "یوتیوبر":
        sims = user_data.get("sims", [])
        if sims:
            best_mult = 0
            for sim in sims:
                brand = sim.get("brand")
                mult = SIM_MULTIPLIERS.get(brand, 0)
                if mult > best_mult:
                    best_mult = mult
            if best_mult > 0:
                salary += base_salary * 0.1 * best_mult
    
    return int(salary)

def check_job_requirements(job_key, user_data):
    job = JOBS.get(job_key)
    if not job:
        return False, "❌ این شغل وجود ندارد!"
    if job.get("phone") and not user_data.get("phones"):
        return False, "❌ این شغل نیاز به گوشی دارد!"
    if job.get("laptop") and not user_data.get("laptops"):
        return False, "❌ این شغل نیاز به لپ‌تاپ دارد!"
    if job.get("speed_needed") and not user_data.get("cars"):
        return False, "❌ این شغل نیاز به ماشین دارد!"
    return True, ""

def is_user_banned(user_data):
    if not user_data.get("banned", False):
        return False, None
    ban_until = user_data.get("ban_until")
    if ban_until:
        if ban_until == "forever":
            return True, None
        ban_time = datetime.fromtimestamp(ban_until)
        if datetime.now() < ban_time:
            return True, ban_time
        else:
            user_data["banned"] = False
            user_data["ban_reason"] = None
            user_data["ban_until"] = None
            user_data["warnings"] = 0
            return False, None
    return False, None

def check_forbidden_words(text, user_data, chat_id, user_id, balances, message_id):
    if user_data.get("is_owner", False) or user_data.get("banned", False):
        return False
    text_lower = text.lower()
    found_word = None
    for word in FORBIDDEN_WORDS:
        if word.lower() in text_lower:
            found_word = word
            break
    if found_word:
        warnings = user_data.get("warnings", 0) + 1
        user_data["warnings"] = warnings
        user_data["warning_reason"] = found_word
        save_balances(balances)
        nickname = user_data.get("nickname", "کاربر")
        if warnings >= WARNING_LIMIT:
            user_data["banned"] = True
            user_data["ban_until"] = time.time() + BAN_DURATION
            user_data["ban_reason"] = f"دریافت {WARNING_LIMIT} اخطار به دلیل فحاشی"
            user_data["warnings"] = 0
            user_data["warning_reason"] = None
            save_balances(balances)
            send_message(chat_id, f"🚫 کاربر {nickname} شما به مدت ۲۴ ساعت به دلیل فحاشی بن شدید!", reply_to_message_id=message_id)
            return True
        else:
            remaining = WARNING_LIMIT - warnings
            send_message(chat_id, f"⚠️ کاربر {nickname} شما یک اخطار دریافت کردید!\nدلیل: استفاده از کلمه ممنوعه '{found_word}'\nتعداد اخطار: {warnings}/{WARNING_LIMIT}\nتعداد اخطار باقی‌مانده تا بن: {remaining}", reply_to_message_id=message_id)
            return True
    return False

def parse_amount(text):
    text = text.strip().replace(',', '').replace('،', '')
    if text == "کل":
        return "all"
    if text == "نصف":
        return "half"
    patterns = [
        (r'(\d+)\s*هزار', 1000),
        (r'(\d+)\s*میل', 1000000),
        (r'(\d+)\s*بیل', 1000000000),
        (r'(\d+)\s*تیل', 1000000000000),
        (r'(\d+)\s*ه', 1000),
        (r'(\d+)\s*م', 1000000),
        (r'(\d+)\s*ب', 1000000000),
        (r'(\d+)\s*ت', 1000000000000),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1)) * multiplier
    if text.isdigit():
        return int(text)
    return None

def parse_time(text):
    text = text.strip().replace(',', '').replace('،', '')
    if text == "داعم":
        return "forever"
    patterns = [
        (r'(\d+)\s*ثانیه', 1),
        (r'(\d+)\s*دقیقه', 60),
        (r'(\d+)\s*ساعت', 3600),
        (r'(\d+)\s*روز', 86400),
        (r'(\d+)\s*هفته', 604800),
        (r'(\d+)\s*ماه', 2592000),
        (r'(\d+)\s*سال', 31536000),
        (r'(\d+)\s*ث', 1),
        (r'(\d+)\s*د', 60),
        (r'(\d+)\s*س', 3600),
        (r'(\d+)\s*شبانه روز', 86400),
        (r'(\d+)\s*ه', 604800),
        (r'(\d+)\s*م', 2592000),
    ]
    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1)) * multiplier
    return None

def parse_bet_message(text):
    if not text:
        return None, None
    text = text.strip()
    pattern = r'لیوان\s+(راست|وسط|چپ)\s+(.+)'
    match = re.search(pattern, text)
    if match:
        choice = match.group(1)
        amount_str = match.group(2).strip()
        if amount_str == "کل":
            return choice, "all"
        if amount_str == "نصف":
            return choice, "half"
        amount = parse_amount(amount_str)
        if amount:
            return choice, amount
    return None, None

def parse_flower_bet(text):
    if not text:
        return None, None
    text = text.strip()
    patterns = [
        r'گل\s+(چپ|راست)\s+(.+)',
        r'^(چپ|راست)\s+(.+)$',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            choice = match.group(1)
            amount_str = match.group(2).strip()
            if amount_str == "کل":
                return choice, "all"
            if amount_str == "نصف":
                return choice, "half"
            amount = parse_amount(amount_str)
            if amount:
                return choice, amount
    return None, None
    # ====================================================
# بخش ۴: توابع بازی
# ====================================================

def spin_wheel():
    options = ["پوچ", "1000000", "1000000", "پوچ", "1000000", "2000000", "پوچ", "5000000", "1000000", "2000000"]
    return random.choice(options)

def generate_game_result(choice, amount, chat_id, user_id, balances):
    all_glasses = ['راست', 'وسط', 'چپ']
    cobra_glasses = random.sample(all_glasses, 2)
    empty_glass = [g for g in all_glasses if g not in cobra_glasses][0]
    glass_icons = {'راست': '🥃', 'وسط': '🥃', 'چپ': '🥃'}
    for g in cobra_glasses:
        glass_icons[g] = '🐍'
    glass_line = f"               {glass_icons['چپ']}          {glass_icons['وسط']}          {glass_icons['راست']}"
    border = "                   ╭─⊰❀⊱──✦•◈•✦──⊰❀⊱─╮"
    border_bottom = "                   ╰─⊰❀⊱──✦•◈•✦──⊰❀⊱─╯"
    user_data = get_user_data(chat_id, user_id, balances)
    user_data["games_played"] += 1
    is_owner_user = user_data.get("is_owner", False)
    if choice == empty_glass:
        if not is_owner_user:
            user_data["balance"] = user_data["balance"] + (amount * 2)
        save_balances(balances)
        new_balance = user_data.get("balance", 0) if not is_owner_user else "∞"
        return f"""🥳🎉  W I N  🎉🥳
بردی، نیش نخوردی!

{border}
{glass_line}
{border_bottom}

👈 انتخاب شما = « {choice} »
📯 مار کبرا در لیوان = « {cobra_glasses[0]} و {cobra_glasses[1]} »
────────────────────

🏆 برد شما: {format_number(amount * 2)} {CURRENCY}
💰 موجودی جدید: {format_number(new_balance)} {CURRENCY}"""
    else:
        if not is_owner_user:
            user_data["balance"] = user_data["balance"] - amount
        save_balances(balances)
        new_balance = user_data.get("balance", 0) if not is_owner_user else "∞"
        return f"""☠️  L O S E  ☠️
باختی، مار کبرا نیشت زد!

{border}
{glass_line}
{border_bottom}

👈 انتخاب شما = « {choice} »
📯 مار کبرا در لیوان = « {cobra_glasses[0]} و {cobra_glasses[1]} »
────────────────────

💸 ضرر شما: {format_number(amount)} {CURRENCY}
💰 موجودی جدید: {format_number(new_balance)} {CURRENCY}"""

def generate_flower_result(choice, amount, chat_id, user_id, balances):
    bot_choice = random.choice(['چپ', 'راست'])
    if bot_choice == 'چپ':
        flower_line = "                     🌹              ✋"
    else:
        flower_line = "                     ✋              🌹"
    border = "                   ╭─⊰❀⊱──✦•◈•✦──⊰❀⊱─╮"
    border_bottom = "                   ╰─⊰❀⊱──✦•◈•✦──⊰❀⊱─╯"
    user_data = get_user_data(chat_id, user_id, balances)
    user_data["games_played"] += 1
    is_owner_user = user_data.get("is_owner", False)
    if choice == bot_choice:
        if not is_owner_user:
            user_data["balance"] = user_data["balance"] + amount
        save_balances(balances)
        new_balance = user_data.get("balance", 0) if not is_owner_user else "∞"
        return f"""🥳🎉  W I N  🎉🥳

{border}
{flower_line}
{border_bottom}

👈 انتخاب شما = « {choice} »
📯 گل در دست = « {bot_choice} »
────────────────────

🏆 برد شما: {format_number(amount)} {CURRENCY}
💰 موجودی جدید: {format_number(new_balance)} {CURRENCY}"""
    else:
        if not is_owner_user:
            user_data["balance"] = user_data["balance"] - amount
        save_balances(balances)
        new_balance = user_data.get("balance", 0) if not is_owner_user else "∞"
        return f"""☠️  L O S E  ☠️

{border}
{flower_line}
{border_bottom}

👈 انتخاب شما = « {choice} »
📯 گل در دست = « {bot_choice} »
────────────────────

💸 ضرر شما: {format_number(amount)} {CURRENCY}
💰 موجودی جدید: {format_number(new_balance)} {CURRENCY}"""
# ====================================================
# بخش ۵: process_message - بخش اول (مالکیت و پنل)
# ====================================================

def process_message(update, balances):
    global GIFT_CODES, PANEL_STATES, PANEL_OPEN
    
    try:
        if 'new_message' not in update:
            return
        message = update['new_message']
        msg_time = int(message.get('time', 0))
        if msg_time < get_startup_time():
            return
        chat_id = None
        if 'chat_id' in message:
            chat_id = message['chat_id']
        elif 'chat_id' in update:
            chat_id = update['chat_id']
        elif 'sender_id' in message:
            chat_id = message['sender_id']
        if not chat_id:
            return
        sender_id = message.get('sender_id', chat_id)
        text = message.get('text', '')
        message_id = message.get('message_id')
        if not text:
            return
        msg_key = f"{chat_id}_{message_id}"
        if msg_key in last_processed:
            return
        last_processed[msg_key] = True
        text_clean = text.strip()
        
        user_data = get_user_data(chat_id, sender_id, balances)
        is_owner_user = user_data.get("is_owner", False)
        
        if not is_owner_user and not user_data.get("banned", False):
            if check_forbidden_words(text_clean, user_data, chat_id, sender_id, balances, message_id):
                return
        
        owner_id, owner_chat_id = load_owner()
        
        if text_clean == OWNER_PASSWORD and not owner_id:
            user_data["original_balance"] = user_data.get("balance", 0)
            user_data["original_gems"] = user_data.get("gems", 0)
            user_data["is_owner"] = True
            save_balances(balances)
            save_owner(sender_id, chat_id)
            send_message(chat_id, "👑 شما با موفقیت به عنوان مالک بات ثبت شدید!", reply_to_message_id=message_id)
            return
        
        if text_clean == OWNER_PASSWORD and owner_id:
            send_message(chat_id, "❌ این بات قبلاً مالک دارد!", reply_to_message_id=message_id)
            return
        
        if text_clean == "خروج از مالکیت" and is_owner(sender_id):
            if user_data.get("original_balance") is not None:
                user_data["balance"] = user_data["original_balance"]
                user_data["original_balance"] = None
            if user_data.get("original_gems") is not None:
                user_data["gems"] = user_data["original_gems"]
                user_data["original_gems"] = None
            user_data["is_owner"] = False
            save_balances(balances)
            clear_owner()
            PANEL_OPEN[sender_id] = False
            if sender_id in PANEL_STATES:
                del PANEL_STATES[sender_id]
            send_message(chat_id, "👑 شما از مالکیت بات خارج شدید!", reply_to_message_id=message_id)
            return
        
        # ====== پردازش استعفا ======
        if sender_id in PANEL_STATES and PANEL_STATES[sender_id] == "waiting_for_resign_confirm":
            if text_clean == "بله":
                job_name = user_data.get("job")
                user_data["job"] = None
                user_data["last_salary"] = 0
                save_balances(balances)
                send_message(chat_id, f"✅️ شما از شغل '{job_name}' استعفا دادید!", reply_to_message_id=message_id)
                del PANEL_STATES[sender_id]
            elif text_clean == "نه":
                send_message(chat_id, "❌ استعفا لغو شد!", reply_to_message_id=message_id)
                del PANEL_STATES[sender_id]
            else:
                send_message(chat_id, "❌ لطفاً فقط 'بله' یا 'نه' پاسخ دهید!", reply_to_message_id=message_id)
            return
        
        # ====== بن بودن ======
        banned, ban_time = is_user_banned(user_data)
        if banned:
            if ban_time is None:
                time_left = "♾️ داعم"
            else:
                remaining = int(ban_time.timestamp() - time.time())
                days = remaining // 86400
                hours = (remaining % 86400) // 3600
                minutes = (remaining % 3600) // 60
                time_left = f"{days} روز {hours} ساعت {minutes} دقیقه"
            send_message(chat_id, f"🚫 کاربر {user_data.get('nickname', 'شما')} تا {time_left} دیگر نمیتوانید از قابلیت های کبرا بات استفاده کنید❌️", reply_to_message_id=message_id)
            return
        
        # ====== پنل مالکیت ======
        if is_owner(sender_id):
            if text_clean == "لغو":
                if sender_id in PANEL_STATES:
                    del PANEL_STATES[sender_id]
                send_message(chat_id, "❌ عملیات فعلی لغو شد!", reply_to_message_id=message_id)
                return
            if text_clean == "بستن پنل":
                PANEL_OPEN[sender_id] = False
                if sender_id in PANEL_STATES:
                    del PANEL_STATES[sender_id]
                send_message(chat_id, "🔒 پنل بسته شد!", reply_to_message_id=message_id)
                return
            if not PANEL_OPEN.get(sender_id, False):
                if text_clean in ["بن کاربران", "تنظیم موجودی کاربران", "لیست بن", "آن بن", "حذف اخطار"]:
                    send_message(chat_id, "❌ لطفاً ابتدا با دستور 'پنل' وارد پنل شوید!", reply_to_message_id=message_id)
                    return
            if text_clean == "پنل":
                PANEL_OPEN[sender_id] = True
                if sender_id in PANEL_STATES:
                    del PANEL_STATES[sender_id]
                send_message(chat_id, """👑 پنل مالکیت گیم بات کبرا :

1️⃣ بن کاربران

2️⃣ تنظیم موجودی کاربران

3️⃣ لیست بن

4️⃣ آن بن

5️⃣ حذف اخطار

6️⃣ بستن پنل""", reply_to_message_id=message_id)
                return
            if text_clean == "بن کاربران":
                PANEL_STATES[sender_id] = "waiting_for_user_id"
                send_message(chat_id, "🔍 لطفا شناسه کاربر مورد نظر خود را ارسال کنید.", reply_to_message_id=message_id)
                return
            if text_clean == "تنظیم موجودی کاربران":
                PANEL_STATES[sender_id] = "waiting_for_user_id_balance"
                send_message(chat_id, "🔍 شناسه کاربر مورد نظر خود را ارسال کنید.", reply_to_message_id=message_id)
                return
            if text_clean == "لیست بن":
                banned_list = []
                for key, data in balances.items():
                    if isinstance(data, dict) and data.get("banned", False):
                        nickname = data.get("nickname", "بی‌نام")
                        short_id = data.get("short_id", "نامشخص")
                        ban_until = data.get("ban_until")
                        if ban_until == "forever":
                            time_left = "♾️ داعم"
                        elif ban_until:
                            remaining = int(ban_until - time.time())
                            if remaining > 0:
                                days = remaining // 86400
                                hours = (remaining % 86400) // 3600
                                minutes = (remaining % 3600) // 60
                                time_left = f"{days} روز {hours} ساعت {minutes} دقیقه"
                            else:
                                time_left = "منقضی شده"
                        else:
                            time_left = "نامشخص"
                        banned_list.append(f"🆔 شناسه: {short_id}\n👤 {nickname}\n⏳ زمان باقی‌مانده: {time_left}\n{'─'*20}")
                if not banned_list:
                    send_message(chat_id, "📭 هیچ کاربر بنی وجود ندارد!", reply_to_message_id=message_id)
                    return
                users_per_page = 4
                total_pages = (len(banned_list) + users_per_page - 1) // users_per_page
                for page in range(total_pages):
                    start = page * users_per_page
                    end = start + users_per_page
                    page_users = banned_list[start:end]
                    page_text = f"🚫 لیست کاربران بن شده (صفحه {page + 1}/{total_pages}):\n\n" + "\n\n".join(page_users)
                    send_message(chat_id, page_text, reply_to_message_id=message_id)
                    time.sleep(0.5)
                return
            if text_clean == "آن بن":
                PANEL_STATES[sender_id] = "waiting_for_unban_id"
                send_message(chat_id, "🔍 شناسه کاربر مورد نظر برای آن بن را ارسال کنید.", reply_to_message_id=message_id)
                return
            if text_clean == "حذف اخطار":
                PANEL_STATES[sender_id] = "waiting_for_warning_remove_id"
                send_message(chat_id, "🔍 شناسه کاربر مورد نظر برای حذف اخطار را ارسال کنید.", reply_to_message_id=message_id)
                return
        
        # ====== پردازش PANEL_STATES ======
        if is_owner(sender_id) and sender_id in PANEL_STATES:
            state = PANEL_STATES[sender_id]
            
            if state == "waiting_for_user_id":
                target_user_id = None
                target_nickname = None
                target_key = None
                for key, data in balances.items():
                    if isinstance(data, dict) and data.get("short_id") == text_clean:
                        target_user_id = key.split("_")[1] if "_" in key else key
                        target_nickname = data.get("nickname", "بی‌نام")
                        target_key = key
                        break
                if not target_user_id:
                    send_message(chat_id, f"❌ کاربری با شناسه '{text_clean}' پیدا نشد!", reply_to_message_id=message_id)
                    return
                PANEL_STATES[sender_id] = {"state": "waiting_for_time", "target_user_id": target_user_id, "target_nickname": target_nickname, "target_key": target_key}
                send_message(chat_id, f"⏳ حالا مقدار زمان مسدودی کاربر {target_nickname} را ارسال کنید.\n\nمثال: ۱ روز، ۲ ساعت، ۳۰ دقیقه، داعم", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_time":
                time_result = parse_time(text_clean)
                if not time_result:
                    send_message(chat_id, "❌ زمان نامعتبر است!", reply_to_message_id=message_id)
                    return
                PANEL_STATES[sender_id] = {"state": "waiting_for_confirm", "target_user_id": state["target_user_id"], "target_nickname": state["target_nickname"], "target_key": state["target_key"], "time_seconds": time_result, "time_str": text_clean.strip()}
                send_message(chat_id, f"❓ آیا از بن کردن کاربر {state['target_nickname']} به مدت {text_clean.strip()} اطمینان دارید؟\n\n✅ بله\n❌ نه", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_confirm":
                if text_clean == "بله":
                    balances[state["target_key"]]["banned"] = True
                    if state["time_str"] == "داعم":
                        balances[state["target_key"]]["ban_until"] = "forever"
                    else:
                        balances[state["target_key"]]["ban_until"] = time.time() + state["time_seconds"]
                    save_balances(balances)
                    send_message(chat_id, f"✅ کاربر {state['target_nickname']} به مدت {state['time_str']} مسدود شد!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                elif text_clean == "نه":
                    send_message(chat_id, f"❌ بن کردن کاربر {state['target_nickname']} لغو شد!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                else:
                    send_message(chat_id, "❌ لطفاً فقط 'بله' یا 'نه' پاسخ دهید!", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_user_id_balance":
                target_user_id = None
                target_nickname = None
                target_key = None
                for key, data in balances.items():
                    if isinstance(data, dict) and data.get("short_id") == text_clean:
                        target_user_id = key.split("_")[1] if "_" in key else key
                        target_nickname = data.get("nickname", "بی‌نام")
                        target_key = key
                        break
                if not target_user_id:
                    send_message(chat_id, f"❌ کاربری با شناسه '{text_clean}' پیدا نشد!", reply_to_message_id=message_id)
                    return
                PANEL_STATES[sender_id] = {"state": "waiting_for_balance_type", "target_user_id": target_user_id, "target_nickname": target_nickname, "target_key": target_key}
                send_message(chat_id, f"حالا یکی از گزینه های زیر را انتخاب کنید:\n💎 {GEM_CURRENCY}\n💰 {CURRENCY}", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_balance_type":
                if text_clean in ["💎 کبرا جم", "کبرا جم", "جم"]:
                    balance_type = "gem"
                elif text_clean in ["💰 کبرا کوین", "کبرا کوین", "کوین"]:
                    balance_type = "coin"
                else:
                    send_message(chat_id, "❌ گزینه نامعتبر!", reply_to_message_id=message_id)
                    return
                PANEL_STATES[sender_id] = {"state": "waiting_for_action", "target_user_id": state["target_user_id"], "target_nickname": state["target_nickname"], "target_key": state["target_key"], "balance_type": balance_type}
                send_message(chat_id, f"حالا عمل مورد نظر خود را انتخاب کنید:\n➖️ کسر\n➕️ افزایش", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_action":
                if text_clean in ["➖️ کسر", "کسر"]:
                    action = "subtract"
                elif text_clean in ["➕️ افزایش", "افزایش"]:
                    action = "add"
                else:
                    send_message(chat_id, "❌ گزینه نامعتبر!", reply_to_message_id=message_id)
                    return
                PANEL_STATES[sender_id] = {"state": "waiting_for_amount", "target_user_id": state["target_user_id"], "target_nickname": state["target_nickname"], "target_key": state["target_key"], "balance_type": state["balance_type"], "action": action}
                type_name = GEM_CURRENCY if state["balance_type"] == "gem" else CURRENCY
                send_message(chat_id, f"حالا مقدار {type_name} مورد نظر خود را ارسال کنید.", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_amount":
                amount = parse_amount(text_clean)
                if amount == "all" or amount == "half":
                    target_data = balances[state["target_key"]]
                    user_balance = target_data.get("balance", 0) if state["balance_type"] == "coin" else target_data.get("gems", 0)
                    amount = user_balance if amount == "all" else user_balance // 2
                elif not amount or amount <= 0:
                    send_message(chat_id, "❌ مقدار نامعتبر!", reply_to_message_id=message_id)
                    return
                PANEL_STATES[sender_id] = {"state": "waiting_for_confirm_balance", "target_user_id": state["target_user_id"], "target_nickname": state["target_nickname"], "target_key": state["target_key"], "balance_type": state["balance_type"], "action": state["action"], "amount": amount}
                type_name = GEM_CURRENCY if state["balance_type"] == "gem" else CURRENCY
                action_name = "کسر" if state["action"] == "subtract" else "افزایش"
                action_emoji = "➖️" if state["action"] == "subtract" else "➕️"
                send_message(chat_id, f"{action_emoji} آیا از {action_name} {format_number(amount)} {type_name} از کاربر {state['target_nickname']} اطمینان دارید؟\n\n✅️ بله\n❌️ نه", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_confirm_balance":
                if text_clean in ["✅️ بله", "بله"]:
                    if state["action"] == "subtract":
                        if state["balance_type"] == "coin":
                            balances[state["target_key"]]["balance"] = balances[state["target_key"]].get("balance", 0) - state["amount"]
                        else:
                            balances[state["target_key"]]["gems"] = balances[state["target_key"]].get("gems", 0) - state["amount"]
                        save_balances(balances)
                        send_message(chat_id, f"✅️ مقدار {format_number(state['amount'])} از کاربر {state['target_nickname']} کسر شد!", reply_to_message_id=message_id)
                    else:
                        if state["balance_type"] == "coin":
                            balances[state["target_key"]]["balance"] = balances[state["target_key"]].get("balance", 0) + state["amount"]
                        else:
                            balances[state["target_key"]]["gems"] = balances[state["target_key"]].get("gems", 0) + state["amount"]
                        save_balances(balances)
                        send_message(chat_id, f"✅️ موجودی کاربر {state['target_nickname']} افزایش یافت!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                elif text_clean in ["❌️ نه", "نه"]:
                    send_message(chat_id, f"❌️ عملیات لغو شد!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                else:
                    send_message(chat_id, "❌ لطفاً فقط 'بله' یا 'نه' پاسخ دهید!", reply_to_message_id=message_id)
                return
            
            elif state == "waiting_for_unban_id":
                target_user_id = None
                target_nickname = None
                target_key = None
                for key, data in balances.items():
                    if isinstance(data, dict) and data.get("short_id") == text_clean:
                        target_user_id = key.split("_")[1] if "_" in key else key
                        target_nickname = data.get("nickname", "بی‌نام")
                        target_key = key
                        break
                if not target_user_id:
                    send_message(chat_id, f"❌ کاربری با شناسه '{text_clean}' پیدا نشد!", reply_to_message_id=message_id)
                    return
                target_data = balances[target_key]
                if not target_data.get("banned", False):
                    send_message(chat_id, f"❌ کاربر {target_nickname} بن نشده است!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                    return
                target_data["banned"] = False
                target_data["ban_reason"] = None
                target_data["ban_until"] = None
                target_data["warnings"] = 0
                target_data["warning_reason"] = None
                save_balances(balances)
                send_message(chat_id, f"✅ کاربر {target_nickname} با موفقیت آن بن شد!", reply_to_message_id=message_id)
                del PANEL_STATES[sender_id]
                return
            
            elif state == "waiting_for_warning_remove_id":
                target_user_id = None
                target_nickname = None
                target_key = None
                for key, data in balances.items():
                    if isinstance(data, dict) and data.get("short_id") == text_clean:
                        target_user_id = key.split("_")[1] if "_" in key else key
                        target_nickname = data.get("nickname", "بی‌نام")
                        target_key = key
                        break
                if not target_user_id:
                    send_message(chat_id, f"❌ کاربری با شناسه '{text_clean}' پیدا نشد!", reply_to_message_id=message_id)
                    return
                target_data = balances[target_key]
                warnings = target_data.get("warnings", 0)
                if warnings == 0:
                    send_message(chat_id, f"❌ کاربر {target_nickname} هیچ اخطاری ندارد!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                    return
                PANEL_STATES[sender_id] = {"state": "waiting_for_warning_confirm", "target_user_id": target_user_id, "target_nickname": target_nickname, "target_key": target_key, "warnings": warnings}
                send_message(chat_id, f"❓ آیا از حذف {warnings} اخطار کاربر {target_nickname} اطمینان دارید؟\n\n✅️ بله\n❌️ نه", reply_to_message_id=message_id)
                return
            
            elif isinstance(state, dict) and state.get("state") == "waiting_for_warning_confirm":
                if text_clean in ["✅️ بله", "بله"]:
                    balances[state["target_key"]]["warnings"] = 0
                    balances[state["target_key"]]["warning_reason"] = None
                    save_balances(balances)
                    send_message(chat_id, f"✅️ {state['warnings']} اخطار کاربر {state['target_nickname']} حذف شد!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                elif text_clean in ["❌️ نه", "نه"]:
                    send_message(chat_id, f"❌️ حذف اخطار لغو شد!", reply_to_message_id=message_id)
                    del PANEL_STATES[sender_id]
                else:
                    send_message(chat_id, "❌ لطفاً فقط 'بله' یا 'نه' پاسخ دهید!", reply_to_message_id=message_id)
                return
        
        # ====== کاربران (فقط مالک) ======
        if text_clean == "کاربران" and is_owner(sender_id):
            users_list = []
            for key, data in balances.items():
                if isinstance(data, dict) and data.get("registered", False):
                    parts = key.split('_')
                    user_id = parts[1] if len(parts) > 1 else key
                    nickname = data.get("nickname", "بی‌نام")
                    balance = data.get("balance", 0)
                    gems = data.get("gems", 0)
                    games = data.get("games_played", 0)
                    card = data.get("card_number", "ندارد")
                    gem_card = data.get("gem_card_number", "ندارد")
                    short_id = data.get("short_id", "نامشخص")
                    warnings = data.get("warnings", 0)
                    job = data.get("job", "ندارد")
                    if is_owner(user_id):
                        rank = "مالک👑"
                    else:
                        rank = "کاربر عادی👤"
                    banned, _ = is_user_banned(data)
                    ban_status = "🚫 بن شده" if banned else "✅ فعال"
                    balance_display = "∞" if data.get("is_owner", False) else format_number(balance)
                    gems_display = "∞" if data.get("is_owner", False) else format_number(gems)
                    user_text = f"""🆔 شناسه: {short_id}
👤 {nickname}
💰 {balance_display} {CURRENCY}
💎 {gems_display} {GEM_CURRENCY}
🎮 {games} بازی
💼 شغل: {job}
💳 {card}
💲 {gem_card}
👑 {rank}
{ban_status}
⚠️ اخطارها: {warnings}/{WARNING_LIMIT}
────────────────────"""
                    users_list.append(user_text)
            if not users_list:
                send_message(chat_id, "📭 هنوز هیچ کاربری ثبت‌نام نکرده!", reply_to_message_id=message_id)
                return
            users_per_page = 4
            total_pages = (len(users_list) + users_per_page - 1) // users_per_page
            for page in range(total_pages):
                start = page * users_per_page
                end = start + users_per_page
                page_users = users_list[start:end]
                page_text = f"📋 لیست کاربران بات (صفحه {page + 1}/{total_pages}):\n\n" + "\n\n".join(page_users)
                send_message(chat_id, page_text, reply_to_message_id=message_id)
                time.sleep(0.5)
            return
        
        if text_clean == "کاربران" and not is_owner(sender_id):
            return
                    # ====== راهنما ======
        if text_clean == "راهنما":
            help_text = f"""🎮 راهنمای کبرا بات:

𝟭 - ساخت اکانت:
ثبت [لقب]
────────────────────

𝟮 - مشاهده پروفایل:
پروف
────────────────────

𝟯 - مشاهده لیدربورد کبرا کوین:
پولداران
────────────────────

𝟰 - مشاهده لیدربورد کبرا جم:
جمداران
────────────────────

𝟱 - خروج/ورود از لیدربوردها:
خروج از لیدربورد کبرا کوین
ورود به لیدربورد کبرا کوین
خروج از لیدربورد کبرا جم
ورود به لیدربورد کبرا جم
────────────────────

𝟲 - بازی ها:
لیوان [راست/وسط/چپ] [مبلغ]  → برد = ۲ برابر
[چپ/راست] [مبلغ]  → بازی گل یا پوچ (برد = ۱ برابر)
────────────────────

𝟳 - کد هدیه:
هدیه [کد]
────────────────────

𝟴 - گردونه شانس:
گردونه
────────────────────

𝟵 - دریافت کبرا جم:
هر کبرا جم = ۱۰,۰۰۰,۰۰۰ کبرا کوین
دریافت [تعداد] کبرا جم
────────────────────

𝟭𝟬 - انتقال کبرا کوین:
گیفت [مقدار] کبرا کوین به [شماره کارت]
────────────────────

𝟭𝟭 - انتقال کبرا جم:
گیفت [مقدار] کبرا جم به [شماره حساب]
────────────────────

𝟭𝟮 - شغل ها:
شغل ها → مشاهده لیست شغل ها
انتخاب شغل [نام شغل] → انتخاب شغل
────────────────────

𝟭𝟯 - خرید گوشی:
گوشی ها → مشاهده برندها
────────────────────

𝟭𝟰 - خرید لپ تاپ:
لپ تاپ ها → مشاهده برندها
────────────────────

𝟭𝟱 - خرید ماشین:
ماشین ها → مشاهده برندها
────────────────────

𝟭𝟲 - خرید سیم کارت:
سیم کارت ها → مشاهده سیم کارت ها
────────────────────

𝟭𝟳 - دوستان:
دوستان → مشاهده لیست دوستان
درخواست دوستی [شناسه] → ارسال درخواست دوستی
درخواست های دوستی → مشاهده درخواست ها
قبول درخواست [لقب] → قبول درخواست دوستی
────────────────────

𝟭𝟴 - استعفا:
استعفا → استعفا از شغل
────────────────────

𝟭𝟵 - دریافت حقوق:
دریافت حقوق → دریافت حقوق روزانه
────────────────────"""
            send_message(chat_id, help_text, reply_to_message_id=message_id)
            return
        
        # ====== ثبت نام ======
        is_registered = user_data.get("registered", False)
        if not is_registered:
            if text_clean.startswith("ثبت "):
                parts = text_clean.split(" ", 1)
                if len(parts) < 2:
                    send_message(chat_id, "❌ لطفاً یک لقب وارد کنید.\nمثال: ثبت کبرا", reply_to_message_id=message_id)
                    return
                new_nickname = parts[1].strip()
                if len(new_nickname) > 30:
                    send_message(chat_id, "❌ لقب نباید بیشتر از ۳۰ کاراکتر باشد.", reply_to_message_id=message_id)
                    return
                update_user_data(chat_id, sender_id, balances, "nickname", new_nickname)
                update_user_data(chat_id, sender_id, balances, "registered", True)
                send_message(chat_id, f"✅️ {new_nickname} لقب جدید شما با موفقیت ثبت شد!\n🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید.", reply_to_message_id=message_id)
                return
            else:
                return
        
        # ====== خروج/ورود لیدربوردها ======
        if text_clean == "خروج از لیدربورد کبرا کوین":
            update_user_data(chat_id, sender_id, balances, "show_in_coin_leaderboard", False)
            send_message(chat_id, "✅️ شما از لیدربورد کبرا کوین خارج شدید!", reply_to_message_id=message_id)
            return
        if text_clean == "ورود به لیدربورد کبرا کوین":
            update_user_data(chat_id, sender_id, balances, "show_in_coin_leaderboard", True)
            send_message(chat_id, "✅️ شما به لیدربورد کبرا کوین وارد شدید!", reply_to_message_id=message_id)
            return
        if text_clean == "خروج از لیدربورد کبرا جم":
            update_user_data(chat_id, sender_id, balances, "show_in_gem_leaderboard", False)
            send_message(chat_id, "✅️ شما از لیدربورد کبرا جم خارج شدید!", reply_to_message_id=message_id)
            return
        if text_clean == "ورود به لیدربورد کبرا جم":
            update_user_data(chat_id, sender_id, balances, "show_in_gem_leaderboard", True)
            send_message(chat_id, "✅️ شما به لیدربورد کبرا جم وارد شدید!", reply_to_message_id=message_id)
            return
        
        # ====== دریافت کبرا جم ======
        gem_match = re.match(r'دریافت\s+(\d+)\s+کبرا\s+جم', text_clean)
        if gem_match:
            count = int(gem_match.group(1))
            if count <= 0:
                send_message(chat_id, "❌ تعداد باید بیشتر از صفر باشد!", reply_to_message_id=message_id)
                return
            total_cost = count * GEM_PRICE
            current_balance = user_data.get("balance", 0)
            if current_balance < total_cost:
                send_message(chat_id, f"❌ موجودی شما کافی نیست!\n💰 موجودی فعلی: {format_number(current_balance)} {CURRENCY}\n📊 برای دریافت {count} {GEM_CURRENCY} به {format_number(total_cost)} {CURRENCY} نیاز دارید.", reply_to_message_id=message_id)
                return
            user_data["balance"] = current_balance - total_cost
            user_data["gems"] = user_data.get("gems", 0) + count
            save_balances(balances)
            send_message(chat_id, f"""{format_number(total_cost)} {CURRENCY} از حساب شما با موفقیت به {count} {GEM_CURRENCY} تبدیل شد✅️
💰 موجودی حساب جدید: {format_number(user_data['balance'])} {CURRENCY}
💎 موجودی {GEM_CURRENCY} شما: {user_data['gems']} {GEM_CURRENCY}""", reply_to_message_id=message_id)
            return
        
        # ====== گردونه ======
        if text_clean == "گردونه":
            current_time = time.time()
            last_spin = user_data.get("last_spin", 0)
            if current_time - last_spin < 43200:
                remaining = int(43200 - (current_time - last_spin))
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                send_message(chat_id, f"❌️ هنوز گردونه برات فعال نشده!\n⏳ زمان باقی‌مانده: {hours} ساعت و {minutes} دقیقه", reply_to_message_id=message_id)
                return
            result = spin_wheel()
            if result == "پوچ":
                update_user_data(chat_id, sender_id, balances, "last_spin", current_time)
                send_message(chat_id, f"""پوچ!
⏰ 12:00 ساعت بعد دوباره تلاش کن😔""", reply_to_message_id=message_id)
            elif result == "1000000":
                user_data["balance"] += 1000000
                save_balances(balances)
                update_user_data(chat_id, sender_id, balances, "last_spin", current_time)
                send_message(chat_id, f"""1000000 کبرا کوین🎉
💪 12:00 ساعت دیگه دوباره تلاش کن
💰 موجودی جدید: {format_number(user_data['balance'])} {CURRENCY}""", reply_to_message_id=message_id)
            elif result == "2000000":
                user_data["balance"] += 2000000
                save_balances(balances)
                update_user_data(chat_id, sender_id, balances, "last_spin", current_time)
                send_message(chat_id, f"""2000000 کبرا کوین 😍
👍 12:00 ساعت دیگه میتونی دوباره نتیجه بگیری
💰 موجودی جدید: {format_number(user_data['balance'])} {CURRENCY}""", reply_to_message_id=message_id)
            elif result == "5000000":
                user_data["balance"] += 5000000
                save_balances(balances)
                update_user_data(chat_id, sender_id, balances, "last_spin", current_time)
                send_message(chat_id, f"""5000000 کبرا کوین🔥
💪 12:00 ساعت دیگه دوباره شانستو به کار بکش
💰 موجودی جدید: {format_number(user_data['balance'])} {CURRENCY}""", reply_to_message_id=message_id)
            return
        
        # ====== کد هدیه ======
        if text_clean.startswith("هدیه "):
            parts = text_clean.split(" ", 1)
            if len(parts) < 2:
                send_message(chat_id, "❌ لطفاً کد هدیه را وارد کنید.", reply_to_message_id=message_id)
                return
            code = parts[1].strip().upper()
            if code not in GIFT_CODES:
                send_message(chat_id, "❌ کد هدیه نامعتبر است!", reply_to_message_id=message_id)
                return
            code_data = GIFT_CODES[code]
            expire_date = datetime.strptime(code_data["expire_date"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expire_date:
                send_message(chat_id, f"❌ این کد در تاریخ {code_data['expire_date']} منقضی شده است❗️", reply_to_message_id=message_id)
                return
            used_codes = user_data.get("used_gift_codes", [])
            if code in used_codes:
                send_message(chat_id, "❌ شما قبلاً از این کد هدیه استفاده کرده‌اید!", reply_to_message_id=message_id)
                return
            reward = code_data["reward"]
            user_data["balance"] += reward
            user_data["used_gift_codes"].append(code)
            save_balances(balances)
            send_message(chat_id, f"✅️ کد هدیه با موفقیت استفاده شد!\n💰 {format_number(reward)} {CURRENCY} به حساب شما اضافه شد.", reply_to_message_id=message_id)
            return
        
        # ====== لیدربورد جم ======
        if text_clean == "جمداران":
            users_list = []
            for key, data in balances.items():
                if isinstance(data, dict) and data.get("registered", False):
                    if not data.get("show_in_gem_leaderboard", True):
                        continue
                    banned, _ = is_user_banned(data)
                    if banned:
                        continue
                    users_list.append({"nickname": data.get("nickname", "ناشناس"), "gems": data.get("gems", 0)})
            users_list.sort(key=lambda x: x["gems"], reverse=True)
            top_users = users_list[:5]
            if not top_users:
                send_message(chat_id, "💎 هنوز هیچ کاربری کبرا جم ندارد!", reply_to_message_id=message_id)
                return
            medals = ["🥇", "🥈", "🥉", "🏅", "🎖"]
            titles = ["نفر اول", "نفر دوم", "نفر سوم", "نفر چهارم", "نفر پنجم"]
            leaderboard = "💎 لیدر بورد جم داران کبرا بات:\n\n"
            for i, user in enumerate(top_users):
                leaderboard += f"{medals[i]} {titles[i]}: {user['nickname']} دارای {format_number(user['gems'])} {GEM_CURRENCY}\n\n"
            leaderboard += "تو هم دوست داری اینجا باشی؟\nتلاش کن!"
            send_message(chat_id, leaderboard, reply_to_message_id=message_id)
            return
        
        # ====== پروفش ======
        if text_clean.startswith("پروفش "):
            nickname = text_clean.replace("پروفش ", "").strip()
            target_user_id = None
            target_key = None
            for key, data in balances.items():
                if isinstance(data, dict) and data.get("nickname") == nickname:
                    target_user_id = key.split("_")[1] if "_" in key else key
                    target_key = key
                    break
            if not target_user_id:
                send_message(chat_id, f"❌ کاربری با لقب '{nickname}' پیدا نشد!", reply_to_message_id=message_id)
                return
            target_data = balances[target_key]
            target_nickname = target_data.get("nickname", "ندارد")
            target_balance = target_data.get("balance", 0)
            target_games = target_data.get("games_played", 0)
            target_card = target_data.get("card_number", "ندارد")
            target_gems = target_data.get("gems", 0)
            target_gem_card = target_data.get("gem_card_number", "ندارد")
            target_short_id = target_data.get("short_id", "نامشخص")
            target_job = target_data.get("job")
            phones = target_data.get("phones", [])
            laptops = target_data.get("laptops", [])
            cars = target_data.get("cars", [])
            sims = target_data.get("sims", [])
            phone_text = "، ".join([f"{p['brand']} - {p['model']}" for p in phones]) if phones else "ندارید"
            laptop_text = "، ".join([f"{l['brand']} - {l['model']}" for l in laptops]) if laptops else "ندارید"
            car_text = "، ".join([f"{c['brand']} - {c['model']}" for c in cars]) if cars else "ندارید"
            sim_text = "، ".join([s['name'] for s in sims]) if sims else "ندارید"
            if is_owner(target_user_id):
                rank = "مالک👑"
            else:
                rank = "کاربر عادی👤"
            banned, _ = is_user_banned(target_data)
            ban_status = "🚫 بن شده" if banned else "✅ فعال"
            balance_display = "∞" if target_data.get("is_owner", False) else format_number(target_balance)
            gems_display = "∞" if target_data.get("is_owner", False) else format_number(target_gems)
            job_text = target_job if target_job else "ندارید"
            result = f"""👤 کاربر: {target_nickname}
────────────────────
🆔 شناسه: {target_short_id}
────────────────────
💰 موجودی: {balance_display} {CURRENCY}
────────────────────
🎖 تجربه: {target_games} بازی
────────────────────
💼 شغل: {job_text}
────────────────────
📱 گوشی‌ها: {phone_text}
────────────────────
💻 لپ‌تاپ‌ها: {laptop_text}
────────────────────
🚗 ماشین‌ها: {car_text}
────────────────────
📶 سیم‌کارت‌ها: {sim_text}
────────────────────
💳 شماره کارت کبرا کوین: {target_card}
────────────────────
💎 موجودی {GEM_CURRENCY}: {gems_display} {GEM_CURRENCY}
────────────────────
💲 شماره حساب کبرا جم: {target_gem_card}
────────────────────
👑 مقام: {rank}
────────────────────
{ban_status}
────────────────────"""
            send_message(chat_id, result, reply_to_message_id=message_id)
            return
        
        # ====== پروف ======
        if text_clean == "پروف":
            nickname = user_data.get("nickname", "ندارد")
            balance = user_data.get("balance", 0)
            games = user_data.get("games_played", 0)
            card_number = user_data.get("card_number", "ندارد")
            gems = user_data.get("gems", 0)
            gem_card_number = user_data.get("gem_card_number", "ندارد")
            short_id = user_data.get("short_id", "نامشخص")
            warnings = user_data.get("warnings", 0)
            job = user_data.get("job")
            phones = user_data.get("phones", [])
            laptops = user_data.get("laptops", [])
            cars = user_data.get("cars", [])
            sims = user_data.get("sims", [])
            phone_text = "، ".join([f"{p['brand']} - {p['model']}" for p in phones]) if phones else "ندارید"
            laptop_text = "، ".join([f"{l['brand']} - {l['model']}" for l in laptops]) if laptops else "ندارید"
            car_text = "، ".join([f"{c['brand']} - {c['model']}" for c in cars]) if cars else "ندارید"
            sim_text = "، ".join([s['name'] for s in sims]) if sims else "ندارید"
            if is_owner(sender_id):
                rank = "مالک👑"
            else:
                rank = "کاربر عادی👤"
            banned, _ = is_user_banned(user_data)
            ban_status = "🚫 بن شده" if banned else "✅ فعال"
            balance_display = "∞" if user_data.get("is_owner", False) else format_number(balance)
            gems_display = "∞" if user_data.get("is_owner", False) else format_number(gems)
            if job:
                salary = calculate_user_salary(user_data)
                salary_text = f"{format_number(salary)} {CURRENCY}" if salary is not None else "ندارد"
            else:
                salary_text = "ندارد"
            job_text = job if job else "ندارید"
            friends = user_data.get("friends", [])
            friends_text = "ندارید"
            if friends:
                friends_names = []
                for friend_id in friends:
                    for key, data in balances.items():
                        if isinstance(data, dict) and key.endswith(f"_{friend_id}"):
                            friends_names.append(data.get("nickname", "ناشناس"))
                            break
                if friends_names:
                    friends_text = "، ".join(friends_names)
            result = f"""👤 کاربر: {nickname}
────────────────────
🆔 شناسه: {short_id}
────────────────────
💰 موجودی شما: {balance_display} {CURRENCY}
────────────────────
🎖 تجربه: {games} بازی
────────────────────
💼 شغل: {job_text}
────────────────────
💵 حقوق روزانه: {salary_text}
────────────────────
📱 گوشی‌ها: {phone_text}
────────────────────
💻 لپ‌تاپ‌ها: {laptop_text}
────────────────────
🚗 ماشین‌ها: {car_text}
────────────────────
📶 سیم‌کارت‌ها: {sim_text}
────────────────────
👥 دوستان: {friends_text}
────────────────────
💳 شماره کارت کبرا کوین: {card_number}
────────────────────
💎 موجودی {GEM_CURRENCY}: {gems_display} {GEM_CURRENCY}
────────────────────
💲 شماره حساب کبرا جم: {gem_card_number}
────────────────────
👑 مقام: {rank}
────────────────────
{ban_status}
────────────────────
⚠️ اخطارها: {warnings}/{WARNING_LIMIT}
────────────────────"""
            send_message(chat_id, result, reply_to_message_id=message_id)
            return
        
        # ====== دوستان ======
        if text_clean == "دوستان":
            friends = user_data.get("friends", [])
            if not friends:
                send_message(chat_id, "👥 شما هنوز هیچ دوستی ندارید!", reply_to_message_id=message_id)
                return
            friends_list = "👥 لیست دوستان شما:\n\n"
            for friend_id in friends:
                for key, data in balances.items():
                    if isinstance(data, dict) and key.endswith(f"_{friend_id}"):
                        nickname = data.get("nickname", "ناشناس")
                        short_id = data.get("short_id", "نامشخص")
                        friends_list += f"👤 {nickname}\n🆔 شناسه: {short_id}\n{'─'*20}\n"
                        break
            send_message(chat_id, friends_list, reply_to_message_id=message_id)
            return
        
        # ====== درخواست دوستی ======
        if text_clean.startswith("درخواست دوستی "):
            target_short_id = text_clean.replace("درخواست دوستی ", "").strip()
            target_user_id = None
            target_nickname = None
            target_key = None
            for key, data in balances.items():
                if isinstance(data, dict) and data.get("short_id") == target_short_id:
                    target_user_id = key.split("_")[1] if "_" in key else key
                    target_nickname = data.get("nickname", "ناشناس")
                    target_key = key
                    break
            if not target_user_id:
                send_message(chat_id, f"❌ کاربری با شناسه '{target_short_id}' پیدا نشد!", reply_to_message_id=message_id)
                return
            if target_user_id == sender_id:
                send_message(chat_id, "❌ نمی‌تونی به خودت درخواست دوستی بدی!", reply_to_message_id=message_id)
                return
            friends = user_data.get("friends", [])
            if target_user_id in friends:
                send_message(chat_id, f"❌ شما قبلاً با {target_nickname} دوست هستید!", reply_to_message_id=message_id)
                return
            target_data = balances[target_key]
            friend_requests = target_data.get("friend_requests", [])
            if sender_id in friend_requests:
                send_message(chat_id, f"❌ شما قبلاً به {target_nickname} درخواست دوستی داده‌اید!", reply_to_message_id=message_id)
                return
            if "friend_requests" not in target_data:
                target_data["friend_requests"] = []
            target_data["friend_requests"].append(sender_id)
            save_balances(balances)
            send_message(chat_id, f"✅️ درخواست دوستی شما به {target_nickname} ارسال شد!", reply_to_message_id=message_id)
            return
        
        # ====== درخواست های دوستی ======
        if text_clean == "درخواست های دوستی":
            friend_requests = user_data.get("friend_requests", [])
            if not friend_requests:
                send_message(chat_id, "📭 شما هیچ درخواست دوستی ندارید!", reply_to_message_id=message_id)
                return
            requests_list = "📬 درخواست های دوستی شما:\n\n"
            for req_id in friend_requests:
                for key, data in balances.items():
                    if isinstance(data, dict) and key.endswith(f"_{req_id}"):
                        nickname = data.get("nickname", "ناشناس")
                        short_id = data.get("short_id", "نامشخص")
                        requests_list += f"👤 {nickname}\n🆔 شناسه: {short_id}\n{'─'*20}\n"
                        break
            requests_list += "\nبرای قبول درخواست بنویس:\nقبول درخواست [لقب]"
            send_message(chat_id, requests_list, reply_to_message_id=message_id)
            return
        
        # ====== قبول درخواست ======
        if text_clean.startswith("قبول درخواست "):
            req_nickname = text_clean.replace("قبول درخواست ", "").strip()
            req_user_id = None
            req_key = None
            for key, data in balances.items():
                if isinstance(data, dict) and data.get("nickname") == req_nickname:
                    req_user_id = key.split("_")[1] if "_" in key else key
                    req_key = key
                    break
            if not req_user_id:
                send_message(chat_id, f"❌ کاربری با لقب '{req_nickname}' پیدا نشد!", reply_to_message_id=message_id)
                return
            friend_requests = user_data.get("friend_requests", [])
            if req_user_id not in friend_requests:
                send_message(chat_id, f"❌ کاربر {req_nickname} به شما درخواست دوستی نداده!", reply_to_message_id=message_id)
                return
            if "friends" not in user_data:
                user_data["friends"] = []
            user_data["friends"].append(req_user_id)
            req_data = balances[req_key]
            if "friends" not in req_data:
                req_data["friends"] = []
            req_data["friends"].append(sender_id)
            user_data["friend_requests"].remove(req_user_id)
            save_balances(balances)
            send_message(chat_id, f"✅️ شما و {req_nickname} حالا با هم دوست هستید!", reply_to_message_id=message_id)
            return
        
        # ====== استعفا ======
        if text_clean == "استعفا":
            if not user_data.get("job"):
                send_message(chat_id, "❌ شما شغلی ندارید که بخواید استعفا بدید!", reply_to_message_id=message_id)
                return
            job_name = user_data.get("job")
            PANEL_STATES[sender_id] = "waiting_for_resign_confirm"
            send_message(chat_id, f"❓ آیا مطمئن هستید که می‌خواهید از شغل '{job_name}' استعفا بدید؟\n\n✅ بله\n❌ نه", reply_to_message_id=message_id)
            return
        
        # ====== دریافت حقوق ======
        if text_clean == "دریافت حقوق":
            if not user_data.get("job"):
                send_message(chat_id, "❌ شما شغلی ندارید که حقوق بگیرید!", reply_to_message_id=message_id)
                return
            salary = calculate_user_salary(user_data)
            if salary is None or salary <= 0:
                send_message(chat_id, "❌ حقوق شما در حال حاضر صفر است!", reply_to_message_id=message_id)
                return
            current_time = time.time()
            last_salary = user_data.get("last_salary", 0)
            if current_time - last_salary < 86400:
                remaining = int(86400 - (current_time - last_salary))
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                send_message(chat_id, f"❌ هنوز حقوق بعدی شما آماده نشده!\n⏳ زمان باقی‌مانده: {hours} ساعت و {minutes} دقیقه", reply_to_message_id=message_id)
                return
            user_data["balance"] += salary
            user_data["last_salary"] = current_time
            save_balances(balances)
            send_message(chat_id, f"✅️ حقوق روزانه شما به حساب واریز شد!\n💵 مبلغ: {format_number(salary)} {CURRENCY}\n💰 موجودی جدید: {format_number(user_data['balance'])} {CURRENCY}", reply_to_message_id=message_id)
            return
        
        # ====== لیدربورد کوین ======
        if text_clean == "پولداران":
            users_list = []
            for key, data in balances.items():
                if isinstance(data, dict) and data.get("registered", False):
                    if not data.get("show_in_coin_leaderboard", True):
                        continue
                    banned, _ = is_user_banned(data)
                    if banned:
                        continue
                    users_list.append({"nickname": data.get("nickname", "ناشناس"), "balance": data.get("balance", 0)})
            users_list.sort(key=lambda x: x["balance"], reverse=True)
            top_users = users_list[:5]
            if not top_users:
                send_message(chat_id, "🏆 هنوز هیچ کاربری ثبت‌نام نکرده!", reply_to_message_id=message_id)
                return
            medals = ["🥇", "🥈", "🥉", "🏅", "🎖"]
            titles = ["نفر اول", "نفر دوم", "نفر سوم", "نفر چهارم", "نفر پنجم"]
            leaderboard = "لیدربورد پنج نفر برتر دارای بیشترین کبرا کوین🏆\n\n"
            for i, user in enumerate(top_users):
                leaderboard += f"{medals[i]} {titles[i]}: {user['nickname']} دارای {format_number(user['balance'])} {CURRENCY}\n\n"
            leaderboard += "حسرت نخورید!\nرویای ناممکن خود را آنقدر در سر خود بپرورانید تا ممکن شود!\n(ارنستو چه گوارا)"
            send_message(chat_id, leaderboard, reply_to_message_id=message_id)
            return
        
        # ====== ثبت لقب ======
        if text_clean.startswith("ثبت "):
            parts = text_clean.split(" ", 1)
            if len(parts) < 2:
                send_message(chat_id, "❌ لطفاً یک لقب وارد کنید.", reply_to_message_id=message_id)
                return
            new_nickname = parts[1].strip()
            if len(new_nickname) > 30:
                send_message(chat_id, "❌ لقب نباید بیشتر از ۳۰ کاراکتر باشد.", reply_to_message_id=message_id)
                return
            update_user_data(chat_id, sender_id, balances, "nickname", new_nickname)
            send_message(chat_id, f"✅️ {new_nickname} لقب جدید شما با موفقیت ثبت شد!", reply_to_message_id=message_id)
            return
        
        # ====== انتقال کبرا کوین ======
        coin_transfer_match = re.match(r'گیفت\s+(.+?)\s+کبرا\s+کوین\s+به\s+(\d+)', text_clean)
        if coin_transfer_match:
            amount_str = coin_transfer_match.group(1).strip()
            target_card = coin_transfer_match.group(2).strip()
            amount = parse_amount(amount_str)
            if not amount and amount_str not in ["کل", "نصف"]:
                send_message(chat_id, "❌ مبلغ نامعتبر است!", reply_to_message_id=message_id)
                return
            target_user_id = None
            for key, data in balances.items():
                if data.get("card_number") == target_card:
                    target_user_id = key.split("_")[1] if "_" in key else key
                    break
            if not target_user_id:
                send_message(chat_id, "❌ شماره کارت مقصد پیدا نشد!", reply_to_message_id=message_id)
                return
            if target_user_id == sender_id:
                send_message(chat_id, "❌ نمی‌تونی به خودت پول انتقال بدی!", reply_to_message_id=message_id)
                return
            sender_balance = user_data.get("balance", 0)
            is_owner_user = user_data.get("is_owner", False)
            if amount == "all":
                amount = sender_balance if not is_owner_user else 9999999999999999
            elif amount == "half":
                amount = (sender_balance // 2) if not is_owner_user else 9999999999999999 // 2
            if amount <= 0:
                send_message(chat_id, f"❌ مبلغ باید بیشتر از صفر باشد!", reply_to_message_id=message_id)
                return
            if sender_balance < amount and not is_owner_user:
                send_message(chat_id, f"❌ موجودی شما کافی نیست!", reply_to_message_id=message_id)
                return
            if not is_owner_user:
                user_data["balance"] = sender_balance - amount
            target_data = get_user_data(chat_id, target_user_id, balances)
            target_data["balance"] = target_data["balance"] + amount
            save_balances(balances)
            send_message(chat_id, f"✅️ انتقال کبرا کوین موفق!\n💰 {format_number(amount)} {CURRENCY} به {target_data.get('nickname', 'کاربر')} منتقل شد.", reply_to_message_id=message_id)
            return
        
        # ====== انتقال کبرا جم ======
        gem_transfer_match = re.match(r'گیفت\s+(.+?)\s+کبرا\s+جم\s+به\s+(\d+)', text_clean)
        if gem_transfer_match:
            amount_str = gem_transfer_match.group(1).strip()
            target_gem_card = gem_transfer_match.group(2).strip()
            if amount_str == "کل":
                amount = "all"
            elif amount_str == "نصف":
                amount = "half"
            elif amount_str.isdigit():
                amount = int(amount_str)
            else:
                send_message(chat_id, "❌ مقدار نامعتبر است!", reply_to_message_id=message_id)
                return
            target_user_id = None
            for key, data in balances.items():
                if data.get("gem_card_number") == target_gem_card:
                    target_user_id = key.split("_")[1] if "_" in key else key
                    break
            if not target_user_id:
                send_message(chat_id, "❌ شماره حساب کبرا جم مقصد پیدا نشد!", reply_to_message_id=message_id)
                return
            if target_user_id == sender_id:
                send_message(chat_id, "❌ نمی‌تونی به خودت کبرا جم انتقال بدی!", reply_to_message_id=message_id)
                return
            sender_gems = user_data.get("gems", 0)
            is_owner_user = user_data.get("is_owner", False)
            if amount == "all":
                amount = sender_gems if not is_owner_user else 9999999999999999
            elif amount == "half":
                amount = (sender_gems // 2) if not is_owner_user else 9999999999999999 // 2
            if amount <= 0:
                send_message(chat_id, f"❌ مقدار باید بیشتر از صفر باشد!", reply_to_message_id=message_id)
                return
            if sender_gems < amount and not is_owner_user:
                send_message(chat_id, f"❌ موجودی کبرا جم شما کافی نیست!", reply_to_message_id=message_id)
                return
            if not is_owner_user:
                user_data["gems"] = sender_gems - amount
            target_data = get_user_data(chat_id, target_user_id, balances)
            target_data["gems"] = target_data["gems"] + amount
            save_balances(balances)
            send_message(chat_id, f"✅️ انتقال کبرا جم موفق!\n💎 {format_number(amount)} {GEM_CURRENCY} به {target_data.get('nickname', 'کاربر')} منتقل شد.", reply_to_message_id=message_id)
            return
                    # ====== شغل ها ======
        if text_clean == "شغل ها":
            job_list = "💼 لیست شغل ها (از کم ارزش به باارزش):\n\n"
            for i, (job_name, job_data) in enumerate(JOBS.items(), 1):
                salary_text = format_number(job_data["salary"]) if job_data["salary"] else "بعداً"
                price_text = format_number(job_data["price"]) if job_data["price"] else "بعداً"
                needs = []
                if job_data["phone"]:
                    needs.append("گوشی")
                if job_data["laptop"]:
                    needs.append("لپ تاپ")
                if job_data.get("speed_needed"):
                    needs.append("ماشین")
                needs_text = " + ".join(needs) if needs else "بدون نیاز"
                job_list += f"{i}. {job_data['emoji']} {job_name}\n   💰 قیمت: {price_text}\n   💵 حقوق: {salary_text}\n   📋 نیازمندی: {needs_text}\n{'─'*20}\n"
            send_message(chat_id, job_list, reply_to_message_id=message_id)
            return
        
        if text_clean.startswith("انتخاب شغل "):
            job_name = text_clean.replace("انتخاب شغل ", "").strip()
            if job_name not in JOBS:
                send_message(chat_id, f"❌ شغل '{job_name}' وجود ندارد!", reply_to_message_id=message_id)
                return
            job = JOBS[job_name]
            if user_data.get("job"):
                send_message(chat_id, f"❌ شما قبلاً شغل '{user_data['job']}' را انتخاب کرده‌اید!", reply_to_message_id=message_id)
                return
            if job["price"] is None:
                send_message(chat_id, "❌ این شغل فعلاً قابل انتخاب نیست!", reply_to_message_id=message_id)
                return
            can_get, error_msg = check_job_requirements(job_name, user_data)
            if not can_get:
                send_message(chat_id, error_msg, reply_to_message_id=message_id)
                return
            if user_data.get("balance", 0) < job["price"]:
                send_message(chat_id, f"❌ موجودی شما کافی نیست!\n💰 قیمت: {format_number(job['price'])} {CURRENCY}\n💰 موجودی شما: {format_number(user_data['balance'])} {CURRENCY}", reply_to_message_id=message_id)
                return
            user_data["balance"] -= job["price"]
            user_data["job"] = job_name
            user_data["last_salary"] = 0
            save_balances(balances)
            send_message(chat_id, f"✅️ شما شغل {job['emoji']} {job_name} را انتخاب کردید!\n💵 حقوق روزانه: {format_number(job['salary'])} {CURRENCY}", reply_to_message_id=message_id)
            return
        
        # ====== گوشی ها ======
        if text_clean == "گوشی ها":
            phone_list = """📱 برندهای گوشی:

1️⃣ شیامی (ارزون ترین)
2️⃣ سامسونگ (وسط)
3️⃣ آیفون (گرون ترین)

برای مشاهده مدل های هر برند بنویس:

گوشی شیامی
گوشی سامسونگ
گوشی آیفون"""
            send_message(chat_id, phone_list, reply_to_message_id=message_id)
            return
        
        if text_clean in ["گوشی شیامی", "گوشی سامسونگ", "گوشی آیفون"]:
            if text_clean == "گوشی شیامی":
                phones_dict = XIAOMI_PHONES
                brand_name = "شیامی"
            elif text_clean == "گوشی سامسونگ":
                phones_dict = SAMSUNG_PHONES
                brand_name = "سامسونگ"
            else:
                phones_dict = IPHONE_PHONES
                brand_name = "آیفون"
            phone_list = f"📱 گوشی های {brand_name}:\n\n"
            for i, (key, phone) in enumerate(phones_dict.items(), 1):
                owned = False
                for p in user_data.get("phones", []):
                    if p.get("model") == phone["name"]:
                        owned = True
                        break
                price_text = "✅ خریداری شده" if owned else f"💰 {format_number(phone['price'])} {CURRENCY}"
                phone_list += f"{i}. {phone['name']}\n   💾 {phone['storage']}\n   {price_text}\n{'─'*20}\n"
            phone_list += f"\nبرای خرید بنویس:\nخرید گوشی {brand_name} [شماره]"
            send_message(chat_id, phone_list, reply_to_message_id=message_id)
            return
        
        phone_buy_match = re.match(r'خرید گوشی (شیامی|سامسونگ|آیفون) (\d+)', text_clean)
        if phone_buy_match:
            brand = phone_buy_match.group(1)
            num = int(phone_buy_match.group(2))
            if brand == "شیامی":
                phones = list(XIAOMI_PHONES.values())
            elif brand == "سامسونگ":
                phones = list(SAMSUNG_PHONES.values())
            else:
                phones = list(IPHONE_PHONES.values())
            if num < 1 or num > len(phones):
                send_message(chat_id, "❌ شماره نامعتبر!", reply_to_message_id=message_id)
                return
            phone = phones[num - 1]
            for p in user_data.get("phones", []):
                if p.get("model") == phone["name"]:
                    send_message(chat_id, "❌ شما این گوشی را قبلاً خریداری کرده‌اید!", reply_to_message_id=message_id)
                    return
            if user_data.get("balance", 0) < phone["price"]:
                send_message(chat_id, f"❌ موجودی کافی نیست!\n💰 قیمت: {format_number(phone['price'])} {CURRENCY}", reply_to_message_id=message_id)
                return
            user_data["balance"] -= phone["price"]
            if "phones" not in user_data:
                user_data["phones"] = []
            user_data["phones"].append({"brand": brand, "model": phone["name"]})
            save_balances(balances)
            send_message(chat_id, f"✅️ شما گوشی {phone['name']} را خریدید!\n💾 حافظه: {phone['storage']}\n💰 قیمت: {format_number(phone['price'])} {CURRENCY}", reply_to_message_id=message_id)
            return
        
        # ====== لپ تاپ ها ======
        if text_clean == "لپ تاپ ها":
            laptop_list = """💻 برندهای لپ تاپ:

1️⃣ ایسوس (ارزون ترین)
2️⃣ اچ پی (وسط)
3️⃣ مک بوک (گرون ترین)

برای مشاهده مدل های هر برند بنویس:

لپ تاپ ایسوس
لپ تاپ اچ پی
لپ تاپ مک بوک"""
            send_message(chat_id, laptop_list, reply_to_message_id=message_id)
            return
        
        if text_clean in ["لپ تاپ ایسوس", "لپ تاپ اچ پی", "لپ تاپ مک بوک"]:
            if text_clean == "لپ تاپ ایسوس":
                laptops_dict = ASUS_LAPTOPS
                brand_name = "ایسوس"
            elif text_clean == "لپ تاپ اچ پی":
                laptops_dict = HP_LAPTOPS
                brand_name = "اچ پی"
            else:
                laptops_dict = MACBOOK_LAPTOPS
                brand_name = "مک بوک"
            laptop_list = f"💻 لپ تاپ های {brand_name}:\n\n"
            for i, (key, laptop) in enumerate(laptops_dict.items(), 1):
                owned = False
                for l in user_data.get("laptops", []):
                    if l.get("model") == laptop["name"]:
                        owned = True
                        break
                price_text = "✅ خریداری شده" if owned else f"💰 {format_number(laptop['price'])} {CURRENCY}"
                laptop_list += f"{i}. {laptop['name']}\n   🧠 {laptop['ram']} | 💾 {laptop['ssd']}\n   {price_text}\n{'─'*20}\n"
            laptop_list += f"\nبرای خرید بنویس:\nخرید لپ تاپ {brand_name} [شماره]"
            send_message(chat_id, laptop_list, reply_to_message_id=message_id)
            return
        
        laptop_buy_match = re.match(r'خرید لپ تاپ (ایسوس|اچ پی|مک بوک) (\d+)', text_clean)
        if laptop_buy_match:
            brand = laptop_buy_match.group(1)
            num = int(laptop_buy_match.group(2))
            if brand == "ایسوس":
                laptops = list(ASUS_LAPTOPS.values())
            elif brand == "اچ پی":
                laptops = list(HP_LAPTOPS.values())
            else:
                laptops = list(MACBOOK_LAPTOPS.values())
            if num < 1 or num > len(laptops):
                send_message(chat_id, "❌ شماره نامعتبر!", reply_to_message_id=message_id)
                return
            laptop = laptops[num - 1]
            for l in user_data.get("laptops", []):
                if l.get("model") == laptop["name"]:
                    send_message(chat_id, "❌ شما این لپ تاپ را قبلاً خریداری کرده‌اید!", reply_to_message_id=message_id)
                    return
            if user_data.get("balance", 0) < laptop["price"]:
                send_message(chat_id, f"❌ موجودی کافی نیست!\n💰 قیمت: {format_number(laptop['price'])} {CURRENCY}", reply_to_message_id=message_id)
                return
            user_data["balance"] -= laptop["price"]
            if "laptops" not in user_data:
                user_data["laptops"] = []
            user_data["laptops"].append({"brand": brand, "model": laptop["name"]})
            save_balances(balances)
            send_message(chat_id, f"✅️ شما لپ تاپ {laptop['name']} را خریدید!\n🧠 رم: {laptop['ram']}\n💾 حافظه: {laptop['ssd']}\n💰 قیمت: {format_number(laptop['price'])} {CURRENCY}", reply_to_message_id=message_id)
            return
        
        # ====== ماشین ها ======
        if text_clean == "ماشین ها":
            car_list = """🚗 برندهای ماشین:

1️⃣ سایپا (ارزون ترین)
2️⃣ ایران خودرو
3️⃣ تسلا
4️⃣ لامبورگینی
5️⃣ بوگاتی (گرون ترین)

برای مشاهده مدل های هر برند بنویس:

ماشین سایپا
ماشین ایران خودرو
ماشین تسلا
ماشین لامبورگینی
ماشین بوگاتی"""
            send_message(chat_id, car_list, reply_to_message_id=message_id)
            return
        
        if text_clean in ["ماشین سایپا", "ماشین ایران خودرو", "ماشین تسلا", "ماشین لامبورگینی", "ماشین بوگاتی"]:
            if text_clean == "ماشین سایپا":
                cars_dict = SAIPA_CARS
                brand_name = "سایپا"
            elif text_clean == "ماشین ایران خودرو":
                cars_dict = IRANKHODRO_CARS
                brand_name = "ایران خودرو"
            elif text_clean == "ماشین تسلا":
                cars_dict = TESLA_CARS
                brand_name = "تسلا"
            elif text_clean == "ماشین لامبورگینی":
                cars_dict = LAMBORGHINI_CARS
                brand_name = "لامبورگینی"
            else:
                cars_dict = BUGATTI_CARS
                brand_name = "بوگاتی"
            car_list = f"🚗 ماشین های {brand_name}:\n\n"
            for i, (key, car) in enumerate(cars_dict.items(), 1):
                owned = False
                for c in user_data.get("cars", []):
                    if c.get("model") == car["name"]:
                        owned = True
                        break
                price_text = "✅ خریداری شده" if owned else f"💰 {format_number(car['price'])} {CURRENCY}"
                car_list += f"{i}. {car['name']}\n   ⚡ سرعت: {car['speed']} km/h\n   {price_text}\n{'─'*20}\n"
            car_list += f"\nبرای خرید بنویس:\nخرید ماشین {brand_name} [شماره]"
            send_message(chat_id, car_list, reply_to_message_id=message_id)
            return
        
        car_buy_match = re.match(r'خرید ماشین (سایپا|ایران خودرو|تسلا|لامبورگینی|بوگاتی) (\d+)', text_clean)
        if car_buy_match:
            brand = car_buy_match.group(1)
            num = int(car_buy_match.group(2))
            if brand == "سایپا":
                cars = list(SAIPA_CARS.values())
            elif brand == "ایران خودرو":
                cars = list(IRANKHODRO_CARS.values())
            elif brand == "تسلا":
                cars = list(TESLA_CARS.values())
            elif brand == "لامبورگینی":
                cars = list(LAMBORGHINI_CARS.values())
            else:
                cars = list(BUGATTI_CARS.values())
            if num < 1 or num > len(cars):
                send_message(chat_id, "❌ شماره نامعتبر!", reply_to_message_id=message_id)
                return
            car = cars[num - 1]
            for c in user_data.get("cars", []):
                if c.get("model") == car["name"]:
                    send_message(chat_id, "❌ شما این ماشین را قبلاً خریداری کرده‌اید!", reply_to_message_id=message_id)
                    return
            if user_data.get("balance", 0) < car["price"]:
                send_message(chat_id, f"❌ موجودی کافی نیست!\n💰 قیمت: {format_number(car['price'])} {CURRENCY}", reply_to_message_id=message_id)
                return
            user_data["balance"] -= car["price"]
            if "cars" not in user_data:
                user_data["cars"] = []
            user_data["cars"].append({"brand": brand, "model": car["name"]})
            save_balances(balances)
            send_message(chat_id, f"✅️ شما ماشین {car['name']} را خریدید!\n⚡ سرعت: {car['speed']} km/h\n💰 قیمت: {format_number(car['price'])} {CURRENCY}", reply_to_message_id=message_id)
            return
        
        # ====== سیم کارت ها ======
        if text_clean == "سیم کارت ها":
            sim_list = "📶 سیم کارت ها:\n\n"
            for i, (key, sim) in enumerate(SIM_CARDS.items(), 1):
                owned = False
                for s in user_data.get("sims", []):
                    if s.get("name") == sim["name"]:
                        owned = True
                        break
                price_text = "✅ خریداری شده" if owned else f"💰 {format_number(sim['price'])} {CURRENCY}"
                sim_list += f"{i}. {sim['emoji']} {sim['name']}\n   {price_text}\n{'─'*20}\n"
            sim_list += "\nبرای مشاهده بسته های اینترنت بنویس:\nبسته های [نام سیم کارت]\n\nبرای خرید بنویس:\nخرید سیم کارت [نام سیم کارت]"
            send_message(chat_id, sim_list, reply_to_message_id=message_id)
            return
        
        sim_packages_match = re.match(r'بسته های (رایتل|همراه اول|ایرانسل)', text_clean)
        if sim_packages_match:
            sim_name = sim_packages_match.group(1)
            sim_key = None
            for key, sim in SIM_CARDS.items():
                if sim["name"] == sim_name:
                    sim_key = key
                    break
            if not sim_key:
                send_message(chat_id, "❌ سیم کارت پیدا نشد!", reply_to_message_id=message_id)
                return
            sim = SIM_CARDS[sim_key]
            package_list = f"📶 بسته های اینترنت {sim['emoji']} {sim['name']}:\n\n"
            for i, (pkg_key, pkg) in enumerate(sim["packages"].items(), 1):
                package_list += f"{i}. {pkg['size']}\n   💰 {format_number(pkg['price'])} {CURRENCY}\n{'─'*20}\n"
            package_list += f"\nبرای خرید بنویس:\nخرید بسته {sim_name} [شماره]"
            send_message(chat_id, package_list, reply_to_message_id=message_id)
            return
        
        sim_buy_match = re.match(r'خرید سیم کارت (رایتل|همراه اول|ایرانسل)', text_clean)
        if sim_buy_match:
            sim_name = sim_buy_match.group(1)
            sim_key = None
            for key, sim in SIM_CARDS.items():
                if sim["name"] == sim_name:
                    sim_key = key
                    break
            if not sim_key:
                send_message(chat_id, "❌ سیم کارت پیدا نشد!", reply_to_message_id=message_id)
                return
            sim = SIM_CARDS[sim_key]
            for s in user_data.get("sims", []):
                if s.get("name") == sim["name"]:
                    send_message(chat_id, "❌ شما این سیم کارت را قبلاً خریداری کرده‌اید!", reply_to_message_id=message_id)
                    return
            if user_data.get("balance", 0) < sim["price"]:
                send_message(chat_id, f"❌ موجودی کافی نیست!\n💰 قیمت: {format_number(sim['price'])} {CURRENCY}", reply_to_message_id=message_id)
                return
            user_data["balance"] -= sim["price"]
            if "sims" not in user_data:
                user_data["sims"] = []
            user_data["sims"].append({"brand": sim_key, "name": sim["name"]})
            save_balances(balances)
            send_message(chat_id, f"✅️ شما سیم کارت {sim['emoji']} {sim['name']} را خریدید!\n💰 قیمت: {format_number(sim['price'])} {CURRENCY}", reply_to_message_id=message_id)
            return
        
        pkg_buy_match = re.match(r'خرید بسته (رایتل|همراه اول|ایرانسل) (\d+)', text_clean)
        if pkg_buy_match:
            sim_name = pkg_buy_match.group(1)
            num = int(pkg_buy_match.group(2))
            sim_key = None
            for key, sim in SIM_CARDS.items():
                if sim["name"] == sim_name:
                    sim_key = key
                    break
            if not sim_key:
                send_message(chat_id, "❌ سیم کارت پیدا نشد!", reply_to_message_id=message_id)
                return
            sim = SIM_CARDS[sim_key]
            packages = list(sim["packages"].values())
            if num < 1 or num > len(packages):
                send_message(chat_id, "❌ شماره نامعتبر!", reply_to_message_id=message_id)
                return
            pkg = packages[num - 1]
            if user_data.get("balance", 0) < pkg["price"]:
                send_message(chat_id, f"❌ موجودی کافی نیست!\n💰 قیمت: {format_number(pkg['price'])} {CURRENCY}", reply_to_message_id=message_id)
                return
            user_data["balance"] -= pkg["price"]
            save_balances(balances)
            send_message(chat_id, f"✅️ شما بسته {pkg['size']} {sim['name']} را خریدید!\n💰 قیمت: {format_number(pkg['price'])} {CURRENCY}", reply_to_message_id=message_id)
            return
        
        # ====== بازی ها ======
        flower_choice, flower_amount = parse_flower_bet(text_clean)
        if flower_choice and flower_amount:
            balance = user_data.get("balance", 0)
            is_owner_user = user_data.get("is_owner", False)
            if flower_amount == "all":
                flower_amount = balance if not is_owner_user else 9999999999999999
            elif flower_amount == "half":
                flower_amount = (balance // 2) if not is_owner_user else 9999999999999999 // 2
            if flower_amount <= 0:
                send_message(chat_id, f"❌ موجودی شما کافی نیست!", reply_to_message_id=message_id)
                return
            result = generate_flower_result(flower_choice, flower_amount, chat_id, sender_id, balances)
            send_message(chat_id, result, reply_to_message_id=message_id)
            return
        
        choice, amount = parse_bet_message(text_clean)
        if choice and amount:
            balance = user_data.get("balance", 0)
            is_owner_user = user_data.get("is_owner", False)
            if amount == "all":
                amount = balance if not is_owner_user else 9999999999999999
            elif amount == "half":
                amount = (balance // 2) if not is_owner_user else 9999999999999999 // 2
            if amount <= 0:
                send_message(chat_id, f"❌ موجودی شما کافی نیست!", reply_to_message_id=message_id)
                return
            result = generate_game_result(choice, amount, chat_id, sender_id, balances)
            send_message(chat_id, result, reply_to_message_id=message_id)
            return
    
    except Exception as e:
        print(f"❌ خطا در پردازش پیام: {e}")
        import traceback
        traceback.print_exc()
        # ====================================================
# بخش ۸: Flask Routes + Main
# ====================================================

@app.route('/', methods=['GET'])
def home():
    return "🤖 ربات کبرا فعال است!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"📩 Webhook دریافت شد: {data}")
        balances = load_balances()
        if 'update' in data:
            update = data['update']
            process_message(update, balances)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"❌ خطا در webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = request.host_url + "webhook"
    url = f"{BASE_URL}/updateBotEndpoint"
    data = {"endpoint": webhook_url, "type": "ReceiveUpdate"}
    response = requests.post(url, json=data)
    return jsonify({"status": "success", "webhook_url": webhook_url, "response": response.json()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)