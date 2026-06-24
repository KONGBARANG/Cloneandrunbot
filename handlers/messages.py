import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# ហៅការទាញយក SETTINGS ពី config
from config import settings as SETTINGS

def get_db_connection():
    return SETTINGS.get_db_connection()

async def handle_normal_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return
        
    user_id = message.from_user.id
    text_received = message.text.strip() if message.text else ""
    
    ADMIN_IDS = SETTINGS.ADMIN_IDS
    is_driver = user_id in ADMIN_IDS

    # ========================================================
    # ១. ករណីអតិថិជនចុចប៊ូតុង 📍 ផ្ញើទីតាំង
    # ========================================================
    if message.location:
        lat = message.location.latitude
        lng = message.location.longitude
        google_map_url = f"https://www.google.com/maps?q={lat},{lng}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            SETTINGS.execute_query(
                cursor,
                "SELECT dispatch_id, driver_id, item_details FROM dispatches WHERE customer_id = %s ORDER BY dispatch_id DESC LIMIT 1",
                (user_id,)
            )
            delivery_data = cursor.fetchone()
            
            if delivery_data:
                dispatch_id, driver_id, item_details = delivery_data
                SETTINGS.execute_query(cursor, "UPDATE dispatches SET customer_location = %s WHERE dispatch_id = %s", (google_map_url, dispatch_id))
                conn.commit()
                
                await message.reply_text("📍 ✅ ទីតាំងរបស់អ្នកត្រូវបានបញ្ជូនទៅកាន់អ្នកដឹកជញ្ជូនរួចរាល់ហើយ! សូមរង់ចាំបន្តិចណា។")
                
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
            cursor.close()
            conn.close()
        return

    # ========================================================
    # ២. ករណីអតិថិជនចុចប៊ូតុងចែករំលែកលេខទូរសព្ទ
    # ========================================================
    if message.contact:
        contact_user_id = message.contact.user_id
        phone_number = message.contact.phone_number.replace("+", "")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
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
    # ៣. 🔥 ករណីចុចប៊ូតុងអត្ថបទនៅលើ Keyboard ធម្មតា (ដោះស្រាយរួចរាល់)
    # ========================================================
    
    # 3.1 ប៊ូតុងឆែកមើលអីវ៉ាន់បច្ចុប្បន្ន
    if "ពិនិត្យមើលអីវ៉ាន់បច្ចុប្បន្ន" in text_received:
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
            status_emoji = "🚴" if active_delivery[1] == "កំពុងដឹកជញ្ជូន" else ("⏳" if "30%" in active_delivery[1] else "✅")
            formatted_date = active_delivery[2].strftime('%Y-%m-%d %H:%M') if active_delivery[2] else 'មិនច្បាស់'
            await message.reply_text(
                f"📦 **ព័ត៌មានអីវ៉ាន់របស់អ្នក៖**\n"
                f"📦 ឈ្មោះអីវ៉ាន់៖ `{active_delivery[0]}`\n"
                f"📊 ស្ថានភាព៖ {status_emoji} `{active_delivery[1]}`\n"
                f"📅 កាលបរិច្ឆេទ៖ {formatted_date}"
            )
        else:
            await message.reply_text("📦 ស្ថានភាព៖ មិនទាន់មានអីវ៉ាន់កំពុងដឹកមកជូនអ្នកឡើយទេបាទ។")
        return

    # 3.2 ប៊ូតុងមើលប្រវត្តិដឹកជញ្ជូន (ដោះស្រាយបញ្ហាចុចមិនដើរ)
    if "មើលប្រវត្តិដឹកជញ្ជូន" in text_received:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            SETTINGS.execute_query(
                cursor,
                "SELECT item_details, status, dispatch_date FROM dispatches WHERE customer_id = %s AND status = 'ដឹកជញ្ជូនជោគជ័យ' ORDER BY dispatch_id DESC LIMIT 5",
                (user_id,)
            )
            history = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
            
        if history:
            msg = "📜 **ប្រវត្តិដឹកជញ្ជូន ៥ ដងចុងក្រោយរបស់អ្នក៖**\n\n"
            for i, item in enumerate(history, 1):
                date_str = item[2].strftime('%Y-%m-%d') if item[2] else 'មិនច្បាស់'
                msg += f"{i}. 📦 `{item[0]}` - ✅ រួចរាល់ ({date_str})\n"
            await message.reply_text(msg)
        else:
            await message.reply_text("📜 លោកអ្នកមិនទាន់មានប្រវត្តិដឹកជញ្ជូនជោគជ័យក្នុងប្រព័ន្ធឡើយទេបាទ។")
        return

    # 3.3 ប៊ូតុងជំនួយការ & ទំនាក់ទំនង (ចាប់យកពាក្យគន្លឹះស៊ីគ្នាជាមួយប៊ូតុងទាំងចាស់ទាំងថ្មី)
    if "ជំនួយការ" in text_received or "ទាក់ទង" in text_received:
        help_text = (
            "📞 **ផ្នែកសេវាអតិថិជន និងជំនួយការ៖**\n\n"
            "• ☎️ លេខទូរសព្ទ៖ `096601345`\n"
            "• 💬 Telegram ភ្នាក់ងារ៖ @kbr0003000\n"
            "• ⏰ ម៉ោងធ្វើការ៖ 8:00 AM - 5:00 PM\n\n"
            "💡 លោកអ្នកអាចប្រើប្រាស់មុខងារស្វែងរកអីវ៉ាន់រហ័សតាមរយៈ Command: /track រួចវាយលេខកូដអីវ៉ាន់ក៏បាន។"
        )
        await message.reply_text(help_text)
        return

    # ========================================================
    # ៤. ករណី Driver បញ្ចូលទិន្នន័យដំបូង (Format: លេខទូរសព្ទ - ឈ្មោះអីវ៉ាន់)
    # ========================================================
    if "-" in text_received:
        parts = text_received.split("-", 1)
        customer_phone = parts[0].strip().replace("+", "")
        item_details = parts[1].strip()
        
        if not customer_phone.isdigit() or len(customer_phone) < 8:
            await message.reply_text("❌ ទម្រង់លេខទូរសព្ទមិនត្រូវទេ សូមវាយម្តងទៀត (ឧទាហរណ៍៖ 096601345 - ឈ្មោះអីវ៉ាន់)")
            return
            
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            phone_variant1 = customer_phone
            phone_variant2 = f"855{customer_phone[1:]}" if customer_phone.startswith("0") else customer_phone
            phone_variant3 = f"0{customer_phone[3:]}" if customer_phone.startswith("855") else customer_phone
            
            SETTINGS.execute_query(cursor, "SELECT user_id, first_name FROM users WHERE phone IN (%s, %s, %s)", (phone_variant1, phone_variant2, phone_variant3))
            customer_data = cursor.fetchone()
            
            def make_keyboard(d_id):
                keyboard = [
                    [
                        InlineKeyboardButton("🚴 កំពុងដឹកជញ្ជូន", callback_data=f"statusdeliv_{d_id}")
                    ],
                    [
                        InlineKeyboardButton("⏳ ជិតដល់ហើយ (30%)", callback_data=f"status30_{d_id}"),
                        # InlineKeyboardButton("✅ ដឹកជោគជ័យ", callback_data=f"statusdone_{d_id}")
                    ],
                    [
                        InlineKeyboardButton("✅ ដឹកជញ្ជូនជោគជ័យ", callback_data=f"statusdone_{d_id}")
                    ]
                ]
                return InlineKeyboardMarkup(keyboard)

            if customer_data:
                cust_id, cust_name = customer_data
                SETTINGS.execute_query(cursor, "INSERT INTO dispatches (driver_id, customer_phone, customer_id, item_details) VALUES (%s, %s, %s, %s)", (user_id, customer_phone, cust_id, item_details))
                conn.commit()
                
                dispatch_id = SETTINGS.get_last_insert_id(cursor)
                
                await message.reply_text(
                    f"✅ អតិថិជនចាស់ឈ្មោះ {cust_name} មានក្នុងប្រព័ន្ធ\n🚀 ប្រព័ន្ធបានផ្ញើសារដំណឹងទៅគាត់អូតូហើយ。\n\n👇 សម្រាប់ Driver ប្ដូរស្ថានភាពអីវ៉ាន់នេះ៖",
                    reply_markup=make_keyboard(dispatch_id)
                )
                
                try:
                    notify_text = f"🔔 ជំរាបសួរ លោក/អ្នក {cust_name}!\n📦 អីវ៉ាន់របស់អ្នកគឺ `{item_details}` កុងពុងត្រូវបានដឹកជញ្ជូនមកហើយបាទបាទ។"
                    await context.bot.send_message(chat_id=cust_id, text=notify_text)
                except Exception:
                    pass
            else:
                SETTINGS.execute_query(cursor, "INSERT INTO dispatches (driver_id, customer_phone, item_details) VALUES (%s, %s, %s)", (user_id, customer_phone, item_details))
                conn.commit()
                
                dispatch_id = SETTINGS.get_last_insert_id(cursor)
                bot_username = (await context.bot.get_me()).username
                invite_link = f"https://t.me/{bot_username}?start=dispatch_{dispatch_id}"
                
                await message.reply_text(
                    f"🔍 រកមិនឃើញលេខទូរសព្ទនេះទេ (អតិថិជនថ្មី)!\n👉🔗 សូមផ្ញើ Link នេះទៅកាន់គាត់៖\n{invite_link}\n\n👇 សម្រាប់ Driver ប្ដូរស្ថានភាពអីវ៉ាន់នេះ៖",
                    reply_markup=make_keyboard(dispatch_id)
                )
        finally:
            cursor.close()
            conn.close()
        return

    # ========================================================
    # ៥. បាតក្រោមបង្អស់៖ ឆ្លើយតបការពារការផ្ញើសាររំខាន
    # ========================================================
    if is_driver:
        await message.reply_text("💡 **របៀបប្រើប្រាស់សម្រាប់ Driver:**\n\nសូមបញ្ចូលអីវ៉ាន់ថ្មីតាមទម្រង់៖ `លេខទូរសព្ទ - ឈ្មោះអីវ៉ាន់`\nបន្ទាប់មកប្រព័ន្ធនឹងបង្ហាញប៊ូតុងឱ្យចុចបញ្ជាអូតូ!")
    else:
        await message.reply_text("🙏 សូមអភ័យទោសបាទ! ខ្ញុំជាប្រព័ន្ធស្វ័យប្រវត្តិ។ សូមលោកអ្នកចុចប្រើប្រាស់ប៊ូតុងម៉ឺនុយបញ្ជានៅផ្នែកខាងក្រោម ដើម្បីពិនិត្យមើលអីវ៉ាន់ ឬផ្ញើទីតាំងបាទ។")


# ========================================================
# ៦. មុខងារសម្រាប់ចាប់យកការចុចប៊ូតុង (Inline Button Handler)
# ========================================================
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() 
    
    data = query.data
    user_id = query.from_user.id
    
    if user_id not in SETTINGS.ADMIN_IDS:
        await query.message.reply_text("❌ លោកអ្នកគ្មានសិទ្ធិបញ្ជាប៊ូតុងនេះឡើយ!")
        return

    if "_" in data:
        action, dispatch_id = data.split("_", 1)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            SETTINGS.execute_query(cursor, "SELECT customer_id, item_details FROM dispatches WHERE dispatch_id = %s", (dispatch_id,))
            dispatch_data = cursor.fetchone()
            
            if dispatch_data:
                cust_id, item_details = dispatch_data
                
                if action == "statusdeliv":
                    new_status = "កំពុងដឹកជញ្ជូន"
                    notify_text = (
                        f"🚴 **ដំណឹងពីអ្នកដឹកជញ្ជូន (Driver)!**\n\n"
                        f"អីវ៉ាន់របស់អ្នក៖ `{item_details}` គឺកំពុងដឹកជញ្ជូន។\n"
                        f"📊 ស្ថានភាព៖ 🚴 `កំពុងដឹកជញ្ជូន`\n\n"
                        f"📍 សូមលោកអ្នកត្រៀមខ្លួនទទួលអីវ៉ាន់បាទបាទ!"
                    )
                    confirm_msg = f"🚴 បានប្ដូរស្ថានភាពអីវ៉ាន់ ID: {dispatch_id} ទៅជា [កំពុងដឹកជញ្ជូន] រួចរាល់"
                    next_keyboard = [
                        [
                            InlineKeyboardButton("⏳ ជិតដល់ហើយ (30%)", callback_data=f"status30_{dispatch_id}"),
                            InlineKeyboardButton("✅ ដឹកជញ្ជូនជោគជ័យ", callback_data=f"statusdone_{dispatch_id}")
                        ]
                    ]
                    next_markup = InlineKeyboardMarkup(next_keyboard)
                    
                elif action == "status30":
                    new_status = "ជិតដល់ហើយ (30%)"
                    notify_text = (
                        f"⏳ **ដំណឹងពីអ្នកដឹកជញ្ជូន (Driver)!**\n\n"
                        f"អីវ៉ាន់របស់អ្នក៖ `{item_details}` គឺធ្វើដំណើរបានជិតដល់ហើយ (សល់ចម្ងាយប្រហែល 30% ទៀត)。\n"
                        f"📊 ស្ថានភាព៖ ⏳ `ជិតដល់ហើយ (30%)`\n\n"
                        f"📍 សូមលោកអ្នកត្រៀមខ្លួនទទួលអីវ៉ាន់បាទបាទ!"
                    )
                    confirm_msg = f"⏳ បានប្ដូរស្ថានភាពអីវ៉ាន់ ID: {dispatch_id} ទៅជា [ជិតដល់ហើយ (30%)] រួចរាល់!"
                    next_keyboard = [
                        [
                            InlineKeyboardButton("✅ ដឹកជញ្ជូនជោគជ័យ", callback_data=f"statusdone_{dispatch_id}")
                        ]
                    ]
                    next_markup = InlineKeyboardMarkup(next_keyboard)
                
                elif action == "statusdone":
                    new_status = "ដឹកជញ្ជូនជោគជ័យ"
                    notify_text = (
                        f"📦 **ដំណឹងដឹកជញ្ជូនសប្បាយចិត្ត!**\n\n"
                        f"អីវ៉ាន់របស់អ្នក៖ `{item_details}` ត្រូវបានប្រគល់ជូនរួចរាល់ហើយបាទ。\n"
                        f"📊 ស្ថានភាព៖ ✅ `ដឹកជញ្ជូនជោគជ័យ`\n\n"
                        f"🙏 អរគុណលោកអ្នកដែលបានប្រើប្រាស់សេវាកម្មប្រព័ន្ធដឹកជញ្ជូន GS!"
                    )
                    confirm_msg = f"✅ បានប្ដូរស្ថានភាពអីវ៉ាន់ ID: {dispatch_id} ទៅជា [ដឹកជញ្ជូនជោគជ័យ] រួចរាល់!"
                    next_markup = None  # លុបប៊ូតុងចោលទាំងអស់នៅជំហានចុងក្រោយ
                
                # 💾 រក្សាទុកទិន្នន័យទៅកាន់ Database
                SETTINGS.execute_query(cursor, "UPDATE dispatches SET status = %s WHERE dispatch_id = %s", (new_status, dispatch_id))
                conn.commit()
                
                # 🖥️ កែប្រែផ្ទាំង Chat របស់ Driver តែមួយបន្ទាត់នេះគត់ (ដើម្បីផ្លាស់ប្តូរ ឬលុបប៊ូតុងតាមតម្លៃ next_markup)
                await query.edit_message_text(
                    text=f"{query.message.text}\n\n⚙️ **បច្ចុប្បន្នភាព៖** {confirm_msg}",
                    reply_markup=next_markup
                )
                
                # 🔔 ផ្ញើសារដំណឹងទៅកាន់អតិថិជន
                if cust_id:
                    try:
                        await context.bot.send_message(chat_id=cust_id, text=notify_text)
                    except Exception:
                        pass
            else:
                await query.message.reply_text("❌ រកមិនឃើញទិន្នន័យអីវ៉ាន់នេះក្នុងប្រព័ន្ធឡើយ។")
        finally:
            cursor.close()
            conn.close()