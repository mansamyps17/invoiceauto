import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from weasyprint import HTML
from flask import Flask
import threading
import os
import re
from datetime import datetime

API_TOKEN = os.environ.get('BOT_TOKEN', '8878587093:AAFncmD_3pLSir1paGSUgkzPhNhL4oO40Hg') 
bot = telebot.TeleBot(API_TOKEN)

user_logos = {}
user_attachments = {}
user_titles = {}
user_pdf_names = {}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot កំពុងដំណើរការយ៉ាងរលូន! 🟢"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def get_main_menu_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("បង្កើតវិក្កយបត្រ", callback_data='btn_invoice'),
        InlineKeyboardButton("កំណត់ឈ្មោះ File PDF", callback_data='btn_setfilename'),
        InlineKeyboardButton("ដូរចំណងជើងវិក្កយបត្រ", callback_data='btn_settitle'),
        InlineKeyboardButton("កំណត់ Logo", callback_data='btn_setlogo'),
        InlineKeyboardButton("លុប Logo", callback_data='btn_clearlogo'),
        InlineKeyboardButton("បន្ថែម Attachment", callback_data='btn_addattachment'),
        InlineKeyboardButton("លុប Attachment", callback_data='btn_clearattachment')
    )
    return markup

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = "សួស្តី! សូមជ្រើសរើសជម្រើសខាងក្រោមដើម្បីចាប់ផ្តើម៖"
    bot.reply_to(message, text, reply_markup=get_main_menu_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    
    if call.data == 'btn_invoice':
        bot.answer_callback_query(call.id)
        date_markup = InlineKeyboardMarkup()
        today_str = datetime.now().strftime("%d-%m-%Y")
        date_markup.add(
            InlineKeyboardButton(f"យកថ្ងៃនេះ ({today_str})", callback_data=f"date_today_{today_str}"),
            InlineKeyboardButton("រំលង (មិនដាក់ថ្ងៃទី)", callback_data="date_none")
        )
        bot.send_message(chat_id, "តើអ្នកចង់ប្រើប្រាស់កាលបរិច្ឆេទថ្ងៃណាសម្រាប់វិក្កយបត្រនេះ?", reply_markup=date_markup)
        
    elif call.data.startswith('date_today_') or call.data == 'date_none':
        bot.answer_callback_query(call.id)
        selected_date = call.data.split('_')[-1] if call.data.startswith('date_today_') else ""
        
        if not hasattr(bot, 'temp_dates'):
            bot.temp_dates = {}
        bot.temp_dates[chat_id] = selected_date
        
        date_text = f" (កាលបរិច្ឆេទ៖ {selected_date})" if selected_date else " (អត់មានដាក់ថ្ងៃទី)"
        msg = bot.send_message(
            chat_id,
            f"បានកំណត់កាលបរិច្ឆេទ{date_text}រួចរាល់។\n\nសូមផ្ញើបញ្ជីទំនិញរបស់អ្នកមក (អាចដាក់ ឈ្មោះ - បរិមាណ - ឯកតា - តម្លៃ ឬ ឈ្មោះ - តម្លៃ ក៏បាន)៖\n\nឧទាហរណ៍ ១៖ កៅអី - 2 - ដុំ - 15$\nឧទាហរណ៍ ២៖ តុ - 20000៛"
        )
        bot.register_next_step_handler(msg, generate_invoice)
        
    elif call.data == 'btn_setfilename':
        bot.answer_callback_query(call.id)
        msg = bot.reply_to(call.message, "សូមវាយបញ្ចូលឈ្មោះ File PDF ដែលអ្នកចង់បាន៖")
        bot.register_next_step_handler(msg, save_pdf_filename)
        
    elif call.data == 'btn_settitle':
        bot.answer_callback_query(call.id)
        msg = bot.reply_to(call.message, "សូមវាយបញ្ចូលចំណងជើងថ្មីសម្រាប់វិក្កយបត្ររបស់អ្នក៖")
        bot.register_next_step_handler(msg, save_title)
        
    elif call.data == 'btn_setlogo':
        bot.answer_callback_query(call.id)
        msg = bot.reply_to(call.message, "សូមផ្ញើរូបភាព Logo ផ្ទាល់ខ្លួនរបស់អ្នក៖")
        bot.register_next_step_handler(msg, save_logo)
        
    elif call.data == 'btn_clearlogo':
        bot.answer_callback_query(call.id)
        if chat_id in user_logos and os.path.exists(user_logos[chat_id]):
            try:
                os.remove(user_logos[chat_id])
            except:
                pass
            del user_logos[chat_id]
        bot.send_message(chat_id, "បានលុប Logo ចោលរួចរាល់!", reply_markup=get_main_menu_keyboard())
        
    elif call.data == 'btn_addattachment':
        bot.answer_callback_query(call.id)
        bot.send_message(
            chat_id, 
            "សូមផ្ញើរូបភាព Attachment ចូលមកក្នុងឆាតនេះ (អាចផ្ញើច្រើនសន្លឹកព្រមគ្នាបានតាមចិត្ត)។ ពេលផ្ញើរួចរាល់ សូមវាយពាក្យ /done ដើម្បីបញ្ជាក់។"
        )
        
    elif call.data == 'btn_clearattachment':
        bot.answer_callback_query(call.id)
        if chat_id in user_attachments:
            user_attachments[chat_id] = []
        bot.send_message(chat_id, "បានលុបរូប Attachment ទាំងអស់រួចរាល់!", reply_markup=get_main_menu_keyboard())

@bot.message_handler(commands=['setfilename'])
def ask_pdf_filename(message):
    msg = bot.reply_to(message, "សូមវាយបញ្ចូលឈ្មោះ File PDF ដែលអ្នកចង់បាន៖")
    bot.register_next_step_handler(msg, save_pdf_filename)

def save_pdf_filename(message):
    chat_id = message.chat.id
    if message.text:
        clean_name = re.sub(r'[\\/*?:"<>|]', "", message.text.strip())
        user_pdf_names[chat_id] = clean_name
        bot.reply_to(message, f"បានកំណត់ឈ្មោះ File PDF ជា៖ **{clean_name}.pdf** ជោគជ័យ!", reply_markup=get_main_menu_keyboard())
    else:
        bot.reply_to(message, "សូមបញ្ចូលអត្ថបទជាអក្សរ។")

@bot.message_handler(commands=['settitle'])
def ask_title(message):
    msg = bot.reply_to(message, "សូមវាយបញ្ចូលចំណងជើងថ្មីសម្រាប់វិក្កយបត្ររបស់អ្នក៖")
    bot.register_next_step_handler(msg, save_title)

def save_title(message):
    chat_id = message.chat.id
    if message.text:
        user_titles[chat_id] = message.text.strip()
        bot.reply_to(message, f"បានផ្លាស់ប្តូរចំណងជើងទៅជា៖ {user_titles[chat_id]}", reply_markup=get_main_menu_keyboard())
    else:
        bot.reply_to(message, "សូមបញ្ចូលអត្ថបទជាអក្សរ។")

@bot.message_handler(commands=['setlogo'])
def ask_logo(message):
    msg = bot.reply_to(message, "សូមផ្ញើរូបភាព Logo របស់អ្នក៖")
    bot.register_next_step_handler(msg, save_logo)

def save_logo(message):
    chat_id = message.chat.id
    if message.photo:
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            logo_name = f"logo_{chat_id}.jpg"
            with open(logo_name, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            user_logos[chat_id] = logo_name
            bot.reply_to(message, "រក្សាទុក Logo ជោគជ័យ!", reply_markup=get_main_menu_keyboard())
        except Exception as e:
            bot.reply_to(message, f"មានបញ្ហា: {e}")
    else:
        bot.reply_to(message, "សូមផ្ញើជារូបភាពប៉ុណ្ណោះ។")

@bot.message_handler(commands=['addattachment'])
def ask_attachment(message):
    bot.reply_to(message, "សូមផ្ញើរូបភាព Attachment ចូលមក (អាចផ្ញើច្រើនសន្លឹកព្រមគ្នាបាន)។ ផ្ញើរួចសូមវាយពាក្យ /done៖")

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    chat_id = message.chat.id
    if chat_id not in user_attachments:
        user_attachments[chat_id] = []
        
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        img_name = f"attachment_{chat_id}_{len(user_attachments[chat_id])}.jpg"
        with open(img_name, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        user_attachments[chat_id].append(img_name)
    except Exception as e:
        print(f"Error saving photo: {e}")

@bot.message_handler(commands=['done'])
def finish_attachment(message):
    chat_id = message.chat.id
    count = len(user_attachments.get(chat_id, []))
    if count > 0:
        bot.reply_to(message, f"រក្សាទុក Attachment សរុបចំនួន {count} សន្លឹកជោគជ័យ!", reply_markup=get_main_menu_keyboard())
    else:
        bot.reply_to(message, "មិនទាន់មានរូបភាព Attachment ណាមួយត្រូវបានផ្ញើមកទេ។", reply_markup=get_main_menu_keyboard())

@bot.message_handler(commands=['invoice'])
def ask_for_items_command(message):
    chat_id = message.chat.id
    date_markup = InlineKeyboardMarkup()
    today_str = datetime.now().strftime("%d-%m-%Y")
    date_markup.add(
        InlineKeyboardButton(f"យកថ្ងៃនេះ ({today_str})", callback_data=f"date_today_{today_str}"),
        InlineKeyboardButton("រំលង (មិនដាក់ថ្ងៃទី)", callback_data="date_none")
    )
    bot.send_message(chat_id, "តើអ្នកចង់ប្រើប្រាស់កាលបរិច្ឆេទថ្ងៃណាសម្រាប់វិក្កយបត្រនេះ?", reply_markup=date_markup)

def generate_invoice(message):
    bot.reply_to(message, "កំពុងរៀបចំវិក្កយបត្រ A4 របស់អ្នក... ⏳")
    
    chat_id = message.chat.id
    user_input = message.text
    lines = user_input.split('\n')
    
    table_rows = ""
    total_usd = 0.0
    count = 1
    
    invoice_date = ""
    if hasattr(bot, 'temp_dates') and chat_id in bot.temp_dates:
        invoice_date = bot.temp_dates[chat_id]
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        if line_clean.lower().startswith('date:'):
            invoice_date = line_clean.split(':', 1)[1].strip()
            continue
            
        if '-' in line_clean:
            parts = [p.strip() for p in line_clean.split('-')]
            
            item_name = ""
            qty_str = "1"
            unit_str = ""
            price_str = "0$"
            
            if len(parts) >= 4:
                item_name = parts[0]
                qty_str = parts[1]
                unit_str = parts[2]
                price_str = parts[3].lower()
            elif len(parts) == 2:
                item_name = parts[0]
                qty_str = "1"
                unit_str = ""
                price_str = parts[1].lower()
            else:
                continue
                
            numbers = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", price_str)
            if numbers:
                val = float(numbers[0])
                final_usd = 0.0
                
                if '៛' in price_str or 'រៀល' in price_str or 'riel' in price_str:
                    final_usd = val / 4000.0
                else:
                    final_usd = val
                
                qty_numbers = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", qty_str)
                qty_val = float(qty_numbers[0]) if qty_numbers else 1.0
                
                row_total = final_usd * qty_val
                total_usd += row_total
                
                table_rows += f"""
                <tr>
                    <td>{count}</td>
                    <td class="text-left">{item_name}</td>
                    <td>{qty_str}</td>
                    <td>{unit_str}</td>
                    <td>$ {final_usd:,.2f}</td>
                    <td>$ {row_total:,.2f}</td>
                    <td></td>
                </tr>
                """
                count += 1

    logo_html = ""
    if chat_id in user_logos and os.path.exists(user_logos[chat_id]):
        logo_path = os.path.abspath(user_logos[chat_id])
        logo_html = f'<img src="file://{logo_path}" class="logo" alt="Logo">'
    
    current_title = user_titles.get(chat_id, "វិក្កយបត្រ")
    date_html = f'<p class="invoice-date"><b>កាលបរិច្ឆេទ / Date:</b> {invoice_date}</p>' if invoice_date else ''

    custom_pdf_name = user_pdf_names.get(chat_id, "Invoice_A4")
    file_name_final = f"{custom_pdf_name}.pdf"

    attachments_html = ""
    if chat_id in user_attachments and user_attachments[chat_id]:
        attachments_html += '<div class="attachment-section"><p class="attachment-title">ឯកសារភ្ជាប់ (Attachments):</p><table class="img-table"><tr>'
        idx = 0
        for img_file in user_attachments[chat_id]:
            img_path = os.path.abspath(img_file)
            if os.path.exists(img_path):
                if idx > 0 and idx % 2 == 0:
                    attachments_html += '</tr><tr>'
                attachments_html += f'<td class="img-cell"><img src="file://{img_path}" class="attachment-img" alt="Attachment"></td>'
                idx += 1
        if idx % 2 != 0:
            attachments_html += '<td class="img-cell"></td>'
        attachments_html += '</tr></table></div>'

    font_path = os.path.abspath("Battambang-Regular.ttf")

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @font-face {{
                font-family: 'LocalBattambang';
                src: url('file://{font_path}');
            }}
            @page {{ size: A4; margin: 15mm; }}
            
            body {{ font-family: 'LocalBattambang', sans-serif; font-size: 13px; color: #000; }}
            
            .header-container {{ text-align: center; margin-bottom: 5px; position: relative; height: 80px; }}
            .logo {{ max-height: 80px; max-width: 200px; object-fit: contain; position: absolute; left: 0; top: 0; }}
            h2 {{ color: #000; margin-top: 15px; font-weight: 700; font-size: 20px; text-decoration: underline; }}
            .invoice-date {{ text-align: right; font-size: 13px; margin-bottom: 10px; font-weight: bold; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ border: 1px solid #000; padding: 6px; text-align: center; }}
            th {{ background-color: #f0f0f0; font-weight: 700; }}
            .text-left {{ text-align: left; padding-left: 8px; }}
            .text-right {{ text-align: right; padding-right: 15px; }}
            .total-row td {{ font-weight: bold; background-color: #eef2f5; font-size: 14px; }}
            
            .signatures {{ margin-top: 35px; width: 100%; display: table; }}
            .sig-box {{ display: table-cell; text-align: center; width: 50%; font-weight: bold; }}
            .sig-line {{ margin-top: 60px; }}
            
            .attachment-section {{ margin-top: 25px; page-break-inside: avoid; }}
            .attachment-title {{ font-weight: bold; margin-bottom: 8px; text-decoration: underline; font-size: 12px; }}
            .img-table {{ width: 100%; border-collapse: collapse; border: none; }}
            .img-table td {{ border: none; padding: 6px; vertical-align: middle; text-align: center; }}
            .img-cell {{ width: 50%; }}
            .attachment-img {{ max-width: 95%; max-height: 250px; object-fit: contain; border: 1px solid #ccc; padding: 4px; background-color: #fafafa; }}
        </style>
    </head>
    <body>
        <div class="header-container">
            {logo_html}
            <h2>{current_title}</h2>
        </div>
        
        {date_html}
        
        <table>
            <thead>
                <tr>
                    <th style="width: 5%;">លរ</th>
                    <th style="width: 38%;">បរិយាយ</th>
                    <th style="width: 10%;">បរិមាណ</th>
                    <th style="width: 10%;">ឯកតា</th>
                    <th style="width: 13%;">តម្លៃ ($)</th>
                    <th style="width: 14%;">តម្លៃសរុប ($)</th>
                    <th style="width: 10%;">ផ្សេងៗ</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
                <tr class="total-row">
                    <td colspan="5" class="text-right">សរុបទឹកប្រាក់ (USD)</td>
                    <td>$ {total_usd:,.2f}</td>
                    <td></td>
                </tr>
            </tbody>
        </table>

        <div class="signatures">
            <div class="sig-box">
                <p>Prepared by:</p>
                <p class="sig-line">...................................</p>
            </div>
            <div class="sig-box">
                <p>Approved by:</p>
                <p class="sig-line">...................................</p>
            </div>
        </div>

        {attachments_html}
    </body>
    </html>
    """
    
    try:
        pdf_file = HTML(string=html_content).write_pdf()
        bot.send_document(
            message.chat.id, 
            document=(file_name_final, pdf_file),
            caption=f"វិក្កយបត្រ `{file_name_final}` របស់អ្នកបានបង្កើតរួចរាល់ហើយ! 🎉",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        bot.reply_to(message, f"សុំទោស! មានបញ្ហាក្នុងការបង្កើត PDF: {e}", reply_markup=get_main_menu_keyboard())

if __name__ == "__main__":
    threading.Thread(target=run_web_server).start()
    print("Bot កំពុងដំណើរការ...")
    bot.infinity_polling()
