from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import settings as SETTINGS


def get_db_connection():
    # មុខងារសម្រាប់ភ្ជាប់ទៅកាន់ Online Cloud Database
    return SETTINGS.get_db_connection()

# ========================================================
# 1. បង្កើត និងរៀបចំ DATABASE (SUPABASE POSTGRESQL SETUP)
# ========================================================
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # បង្កើត Table សម្រាប់រក្សាទិន្នន័យអតិថិជន (ប្តូរប្រភេទ ID ទៅជា BIGINT)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            phone TEXT DEFAULT NULL,
            registered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # បង្កើត Table សម្រាប់កត់ត្រាការដឹកជញ្ជូនចាស់ (Orders)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            user_id BIGINT,
            item_name TEXT,
            status TEXT DEFAULT 'កំពុងរៀបចំ',
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)

    # 🔥 Table សម្រាប់ប្រព័ន្ធដឹកជញ្ជូនរហ័សរបស់ Driver (Dispatch System) លើ Cloud
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispatches (
            dispatch_id SERIAL PRIMARY KEY,
            driver_id BIGINT,
            customer_phone TEXT,
            customer_id BIGINT DEFAULT NULL,
            item_details TEXT,
            customer_location TEXT DEFAULT NULL,
            status TEXT DEFAULT 'កំពុងដឹកជញ្ជូន',
            dispatch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

# ដំណើរការបង្កើត Table ភ្លាមៗនៅលើ Supabase Cloud នៅពេលបើកកូដ
init_db()


# ========================================================
# 2. មុខងារ COMMAND /START (ឆែកមើល OLD / NEW USER)
# ========================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    first_name = user.first_name
    username = user.username if user.username else "No_Username"

    # ឆែកមើលថាតើគាត់ចូលតាមរយៈ Link ពិសេស (Deep Linking) របស់ Driver ដែរឬទេ
    args = context.args
    dispatch_id = None
    if args and args[0].startswith("dispatch_"):
        dispatch_id = args[0].replace("dispatch_", "")

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ឆែកមើលទិន្នន័យ User ក្នុង Online Database (ប្រើសញ្ញា %s ជំនួស ?)
    cursor.execute("SELECT phone FROM users WHERE user_id = %s", (user_id,))
    user_data = cursor.fetchone()

    # ករណីទី ១៖ រកមិនឃើញ ID = USER NEW (ចុះឈ្មោះគាត់ចូល Cloud)
    if user_data is None:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s)",
            (user_id, username, first_name)
        )
        conn.commit()
        
        # បើគាត់ចូលមកតាមលីងអីវ៉ាន់ ត្រូវរក្សាទុក ID គាត់ទៅក្នុងទិន្នន័យដឹកជញ្ជូននោះអូតូ
        if dispatch_id:
            cursor.execute("UPDATE dispatches SET customer_id = %s WHERE dispatch_id = %s", (user_id, int(dispatch_id)))
            conn.commit()

        welcome_text = (
            f"👋 សួស្តីសមាជិកថ្មី លោក/អ្នក {first_name}! មកកាន់ប្រព័ន្ធដឹកជញ្ជូន GS។\n\n"
            "🙏 ដើម្បីភាពងាយស្រួលក្នុងការទទួលទិន្នន័យអីវ៉ាន់ និងការទាក់ទងពីអ្នកដឹកជញ្ជូន "
            "សូមចុចប៊ូតុងខាងក្រោមដើម្បីចែករំលែកលេខទូរសព្ទ ឬផ្ញើទីតាំងស្កេនទំនិញ។"
        )
        keyboard = [
            [{"text": "📱 ចែកលេខទូរសព្ទ", "request_contact": True}],
            [{"text": "📍 ផ្ញើទីតាំង", "request_location": True}],
            [{"text": "📦 ពិនិត្យមើលអីវ៉ាន់បច្ចុប្បន្ន"}],
            [{"text": "📞 ទាក់ទងភ្នាក់ងារផ្ទាល់"}]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    # ករណីទី ២៖ រកឃើញ ID = USER OLD (អតិថិជនចាស់)
    else:
        phone_number = user_data[0]
        
        if dispatch_id:
            cursor.execute("UPDATE dispatches SET customer_id = %s WHERE dispatch_id = %s", (user_id, int(dispatch_id)))
            conn.commit()

        # ប្រសិនបើមានអីវ៉ាន់ដែល Driver ទើបតែបញ្ចូលសម្រាប់គាត់
        cursor.execute(
            "SELECT item_details, status FROM dispatches WHERE customer_id = %s OR customer_phone = %s ORDER BY dispatch_id DESC LIMIT 1", 
            (user_id, phone_number)
        )
        active_delivery = cursor.fetchone()

        delivery_info = ""
        if active_delivery:
            delivery_info = f"🔔 ព័ត៌មានអីវ៉ាន់បច្ចុប្បន្ន៖ {active_delivery[0]} ({active_delivery[1]})"
        else:
            delivery_info = "📦 ស្ថានភាព៖ មិនទាន់មានអីវ៉ាន់កំពុងដឹកមកជូនអ្នកឡើយទេ"

        welcome_text = (
            f"🎉 រីករាយដែលបានជួបអ្នកម្តងទៀត លោក/អ្នក {first_name} (អតិថិជនចាស់)!\n"
            f"📞 លេខទូរសព្ទរបស់អ្នក៖ {phone_number if phone_number else 'មិនទាន់ចុះឈ្មោះ'}\n"
            f"----------------------------------------\n"
            f"{delivery_info}\n\n"
            "👉 សូមជ្រើសរើសសេវាកម្ម៖\n"
            "📍 /share_location - ផ្ញើទីតាំងទៅកាន់អ្នកដឹកជញ្ជូន\n"
            "🧾 /scan_location - ស្កេនកន្លែងទំនិញ\n"
            "🔍 /track - តាមដានស្ថានភាពអីវ៉ាន់លម្អិត"
        )
        
        keyboard = [
            ["📦 ពិនិត្យមើលអីវ៉ាន់បច្ចុប្បន្ន"],
            [{"text": "📍 ផ្ញើទីតាំងបច្ចុប្បន្ន (Share Location)", "request_location": True}],
            ["📞 ទាក់ទងភ្នាក់ងារផ្ទាល់"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    cursor.close()
    conn.close()


# ========================================================
# 3. មុខងារ COMMAND /HELP, LOCATION, TRACK
# ========================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "💡 ការណែនាំអំពីបញ្ជា (Commands)៖\n\n"
        "/start - ពិនិត្យមើលគណនី និងប្រវត្តិផ្ញើ\n"
        "/help - មើលការណែនាំឡើងវិញ\n"
        "/share_location - ផ្ញើទីតាំងទៅកាន់អ្នកដឹកជញ្ជូន\n"
        "/scan_location - ស្កេនកន្លែងទំនិញ\n"
        "/track - តាមដានស្ថានភាពអីវ៉ាន់"
    )
    await update.message.reply_text(help_text)

async def share_location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[{"text": "📍 ផ្ញើទីតាំង", "request_location": True}]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "📍 សូមចុចប៊ូតុងខាងក្រោមដើម្បីផ្ញើទីតាំងបច្ចុប្បន្នក្នុងជម្រាបអ្នកដឹកជញ្ជូន។",
        reply_markup=reply_markup
    )

async def scan_location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[{"text": "🧾 ស្កេនទំនិញ", "request_location": True}]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "🧾 សូមចុចប៊ូតុងខាងក្រោមដើម្បីផ្ញើទីតាំងស្កេនទំនិញរបស់អ្នក។",
        reply_markup=reply_markup
    )

async def track_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT item_details, status, dispatch_date FROM dispatches WHERE customer_id = %s ORDER BY dispatch_id DESC LIMIT 1",
        (user_id,)
    )
    active_delivery = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if active_delivery:
        status_emoji = "🚴" if active_delivery[1] == "កំពុងដឹកជញ្ជូន" else "✅"
        # បំប្លែងទម្រង់ថ្ងៃខែឱ្យស្អាតសម្រាប់ PostgreSQL 
        formatted_date = active_delivery[2].strftime('%Y-%m-%d %H:%M') if active_delivery[2] else "មិនច្បាស់"
        await update.message.reply_text(
            f"📦 ព័ត៌មានតាមដានអីវ៉ាន់:\n"
            f"ឈ្មោះអីវ៉ាន់៖ `{active_delivery[0]}`\n"
            f"ស្ថានភាព៖ {status_emoji} `{active_delivery[1]}`\n"
            f"កាលបរិច្ឆេទ៖ {formatted_date}"
        )
    else:
        await update.message.reply_text("📦 មិនមានការដឹកជញ្ជូនពេលនេះទេ។ សូមបញ្ចូលលេខទូរសព្ទ ហើយឈ្មោះអីវ៉ាន់របស់អតិថិជន។")