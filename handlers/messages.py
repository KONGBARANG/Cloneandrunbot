import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes

# 🔥 ហៅការទាញយក SETTINGS ពី config ដើម្បីទាញខ្សែភ្ជាប់ទៅកាន់ Supabase 
from config import settings as SETTINGS

def get_db_connection():
    # មុខងារទាញខ្សែភ្ជាប់ទៅកាន់ Online Cloud Database
    return SETTINGS.get_db_connection()

async def handle_normal_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
        
    user_id = message.from_user.id
    
    # ========================================================
    # ១. ករណីអតិថិជនចុចប៊ូតុង 📍 ផ្ញើទីតាំង (Smart Location)
    # ========================================================
    if message.location:
        lat = message.location.latitude
        lng = message.location.longitude
        # 🔥 កែសម្រួល៖ បង្កើត Link Google Maps ឱ្យត្រូវទម្រង់ស្តង់ដារសកល
        google_map_url = f"https://maps.google.com/?q={lat},{lng}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # ស្វែងរកការដឹកជញ្ជូនចុងក្រោយរបស់អតិថិជនម្នាក់នេះ
            SETTINGS.execute_query(
                cursor,
                "SELECT dispatch_id, driver_id, item_details FROM dispatches WHERE customer_id = %s ORDER BY dispatch_id DESC LIMIT 1",
                (user_id,)
            )
            delivery_data = cursor.fetchone()
            
            if delivery_data:
                dispatch_id, driver_id, item_details = delivery_data
                
                # រក្សាទុកលីងទីតាំងចូល Online Database
                SETTINGS.execute_query(cursor, "UPDATE dispatches SET customer_location = %s WHERE dispatch_id = %s", (google_map_url, dispatch_id))
                conn.commit()
                
                await message.reply_text("📍 ✅ ទីតាំងរបស់អ្នកត្រូវបានបញ្ជូនទៅកាន់អ្នកដឹកជញ្ជូនរួចរាល់ហើយ! សូមរង់ចាំបន្តិចណា។")
                
                # 🔥 ផ្ញើទីតាំង និងលីង Map ទៅកាន់ Telegram របស់អ្នកដឹកជញ្ជូន (Driver) ភ្លាមៗអូតូ
                try:
                    driver_text = (
                        f"🔔 ⚡ ហ្វ្រាំងៗ Driver! អតិថិជនបានផ្ញើទីតាំងមកហើយ៖\n"
                        f"📦 អីវ៉ាន់៖ `{item_details}`\n"
                        f"📍 ទីតាំងនៅលើផែនទី៖ {google_map_url}"
                    )
                    await context.bot.send_message(chat_id=driver_id, text=driver_text)
                    await context.bot.send_location(chat_id=driver_id, latitude=lat, longitude=lng)
                except Exception:
                    pass
            else:
                await message.reply_text("❌ មិនអាចផ្ញើទីតាំងបានទេ ព្រោះប្រព័ន្ធរកមិនឃើញទិន្នន័យដឹកជញ្ជូនរបស់អ្នកឡើយ។")
        finally:
            # 🔥 ការពារ៖ ធានាថា Cursor និង Connection ត្រូវតែបិទជានិច្ច ទោះជាផ្ញើសារជោគជ័យឬអត់
            cursor.close()
            conn.close()
        return

    # ========================================================
    # ២. ករណីអតិថិជនចុចប៊ូតុងចែករំលែកលេខទូរសព្ទ (Contact)
    # ========================================================
    if message.contact:
        contact_user_id = message.contact.user_id
        phone_number = message.contact.phone_number.replace("+", "")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # កែទម្រង់ Query ទៅជា %s សម្រាប់ PostgreSQL
            SETTINGS.execute_query(cursor, "UPDATE users SET phone = %s WHERE user_id = %s", (phone_number, contact_user_id))
            conn.commit()
        finally:
            cursor.close()
            conn.close()
        
        await message.reply_text(
            f"✅ ជោគជ័យ! បានកត់ត្រាលេខទូរសព្ទ `{phone_number}` រួចរាល់។\n"
            "👉 សូមចុចវាយពាក្យបញ្ជា `/start` ម្តងទៀតដើម្បីចូលទៅកាន់ទំព័រដើម។"
        )
        return

    # ========================================================
    # ៣. ករណីចុចប៊ូតុងអត្ថបទនៅលើ Keyboard ធម្មតា
    # ========================================================
    text_received = message.text.strip() if message.text else ""
    
    # ឆែកមើលអីវ៉ាន់បច្ចុប្បន្នសម្រាប់អតិថិជន
    if text_received == "📦 ពិនិត្យមើលអីវ៉ាន់បច្ចុប្បន្ន":
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            SETTINGS.execute_query(
                cursor,
                "SELECT item_details, status, dispatch_date FROM dispatches WHERE customer_id = %s ORDER BY dispatch_id DESC LIMIT 1",
                (user_id,)
            )
            active_delivery = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
        
        if active_delivery:
            status_emoji = "🚴" if active_delivery[1] == "កំពុងដឹកជញ្ជូន" else "✅"
            formatted_date = active_delivery[2].strftime('%Y-%m-%d %H:%M') if active_delivery[2] else 'មិនច្បាស់'
            await message.reply_text(
                f"📦 **ព័ត៌មានអីវ៉ាន់របស់អ្នក៖**\n"
                f" ឈ្មោះអីវ៉ាន់៖ `{active_delivery[0]}`\n"
                f" ស្ថានភាព៖ {status_emoji} `{active_delivery[1]}`\n"
                f"📅 កាលបរិច្ឆេទ៖ {formatted_date}"
            )
        else:
            await message.reply_text("📦 ស្ថានភាព៖ មិនទាន់មានអីវ៉ាន់កំពុងដឹកមកជូនអ្នកឡើយទេបាទ។")
        return

    if text_received == "📞 ទាក់ទងភ្នាក់ងារផ្ទាល់":
        await message.reply_text("📞 លោកអ្នកអាចធ្វើការទាក់ទងទៅកាន់ផ្នែកសេវាអតិថិជនតាមរយៈលេខទូរសព្ទ៖ `012 345 678` ឬតេតាម Telegram @GS_Support បាទ។")
        return

    # ========================================================
    # ៤. ករណី Driver បញ្ចូលទិន្នន័យ (Format: លេខទូរសព្ទ - ឈ្មោះអីវ៉ាន់)
    # ========================================================
    if "-" in text_received:
        parts = text_received.split("-", 1)
        customer_phone = parts[0].strip().replace("+", "")
        item_details = parts[1].strip()
        
        if not customer_phone.isdigit() or len(customer_phone) < 8:
            await message.reply_text("❌ ទម្រង់លេខទូរសព្ទមិនត្រូវទេ! សូមវាយម្តងទៀត (ឧទាហរណ៍៖ 012345678 - ឈ្មោះអីវ៉ាន់)")
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # ស្វែងរកលេខទូរសព្ទបែបឆ្លាតវៃ (ឆែកទាំងទម្រង់មាន 0 និងមាន 855)
            phone_variant1 = customer_phone
            phone_variant2 = f"855{customer_phone[1:]}" if customer_phone.startswith("0") else customer_phone
            phone_variant3 = f"0{customer_phone[3:]}" if customer_phone.startswith("855") else customer_phone
            
            SETTINGS.execute_query(
                cursor,
                "SELECT user_id, first_name FROM users WHERE phone IN (%s, %s, %s)",
                (phone_variant1, phone_variant2, phone_variant3)
            )
            customer_data = cursor.fetchone()
            
            if customer_data:
                cust_id, cust_name = customer_data
                SETTINGS.execute_query(
                    cursor,
                    "INSERT INTO dispatches (driver_id, customer_phone, customer_id, item_details) VALUES (%s, %s, %s, %s)",
                    (user_id, customer_phone, cust_id, item_details)
                )
                conn.commit()
                
                await message.reply_text(f"✅ អតិថិជនចាស់ឈ្មោះ {cust_name} មានក្នុងប្រព័ន្ធ\n🚀 ប្រព័ន្ធបានផ្ញើសារដំណឹងទៅគាត់អូតូហើយ។")
                
                try:
                    notify_text = (
                        f"🔔 ជំរាបសួរ លោក/អ្នក {cust_name}!\n"
                        f"📦 អីវ៉ាន់របស់អ្នកគឺ `{item_details}` កំពុងត្រូវបានដឹកជញ្ជូនមកហើយ។\n\n"
                        f"👇 សូមចុចប៊ូតុងខាងក្រោមដើម្បីផ្ញើទីតាំង 📍 ទៅកាន់អ្នកដឹកជញ្ជូនបាទបាទ🏼"
                    )
                    await context.bot.send_message(chat_id=cust_id, text=notify_text)
                except Exception:
                    await message.reply_text("⚠️ ប្រព័ន្ធមិនអាចផ្ញើសារទៅកាន់អតិថិជនបានទេ ព្រោះគាត់អាចនឹងបិទ Bot ចោល។")
            else:
                # ករណីរកមិនឃើញលេខទូរសព្ទ = អតិថិជនថ្មី (New User)
                SETTINGS.execute_query(
                    cursor,
                    "INSERT INTO dispatches (driver_id, customer_phone, item_details) VALUES (%s, %s, %s)",
                    (user_id, customer_phone, item_details)
                )
                conn.commit()
                
                # ទាញយក ID ចុងក្រោយដែលទើបតែ Insert
                dispatch_id = SETTINGS.get_last_insert_id(cursor)
                
                bot_username = (await context.bot.get_me()).username
                invite_link = f"https://t.me/{bot_username}?start=dispatch_{dispatch_id}"
                
                response_msg = (
                    f"🔍 រកមិនឃើញលេខទូរសព្ទនេះទេ (អតិថិជនថ្មី)!\n\n"
                    f"👉🔗 សូមផ្ញើ Link នេះទៅកាន់គាត់ ដើម្បីឱ្យគាត់ចុច Start និងមើលព័ត៌មាន៖\n\n"
                    f"{invite_link}"
                )
                await message.reply_text(response_msg)
        finally:
            cursor.close()
            conn.close()
        return

    await message.reply_text("💡 ដើម្បីបញ្ចូលអីវ៉ាន់ថ្មី សូមវាយទម្រង់៖ `លេខទូរសព្ទ - ឈ្មោះអីវ៉ាន់`")