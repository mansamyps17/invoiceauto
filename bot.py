import telebot
from weasyprint import HTML
from flask import Flask
import threading
import os
import re

API_TOKEN = os.environ.get('BOT_TOKEN', '8878587093:AAFncmD_3pLSir1paGSUgkzPhNhL4oO40Hg') 
bot = telebot.TeleBot(API_TOKEN)

user_attachments = {}
user_titles = {} # រក្សាទុកចំណងជើងវិក្កយបត្ររបស់ User ម្នាក់ៗ

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot កំពុងដំណើរការយ៉ាងរលូន! 🟢"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ១. មុខងារកែប្រែចំណងជើងវិក្កយបត្រ
@bot.message_handler(commands=['settitle'])
def ask_title(message):
    msg = bot.reply_to(message, "✏️ សូមវាយបញ្ចូលចំណងជើងថ្មីដែលអ្នកចង់ឱ្យបង្ហាញលើវិក្កយបត្រ (ឧទាហរណ៍៖ បញ្ជីទិញឥវ៉ាន់ ឬ វិក្កយបត្រលក់ទំនិញ)：")
    bot.register_next_step_handler(msg, save_title)

def save_title(message):
    chat_id = message.chat.id
    if message.text:
        user_titles[chat_id] = message.text.strip()
        bot.reply_to(message, f"✅ បានផ្លាស់ប្តូរចំណងជើងទៅជា៖ **{user_titles[chat_id]}** ជោគជ័យ!")
    else:
        bot.reply_to(message, "❌ សូមបញ្ចូលអត្ថបទជាអក្សរ។")

# ២. មុខងារកែប្រែ Logo
@bot.message_handler(commands=['setlogo'])
def ask_logo(message):
    msg = bot.reply_to(message, "🖼 សូមផ្ញើរូបភាព Logo ថ្មី៖")
    bot.register_next_step_handler(msg, save_logo)

def save_logo(message):
    if message.photo:
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open("logo.jpg", 'wb') as new_file:
                new_file.write(downloaded_file)
            bot.reply_to(message, "✅ រក្សាទុក Logo ថ្មីជោគជ័យ!")
        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា: {e}")
    else:
        bot.reply_to(message, "❌ សូមផ្ញើជារូបភាពប៉ុណ្ណោះ។")

# ៣. មុខងារបន្ថែម ឬកែប្រែរូបភាព Attachment (អាចលុបរបស់ចាស់ចោលសិនជាមួយ /clearattachment)
@bot.message_handler(commands=['clearattachment'])
def clear_attachment(message):
    chat_id = message.chat.id
    if chat_id in user_attachments:
        user_attachments[chat_id] = []
    bot.reply_to(message, "🗑 បានលុបរូបភាព Attachment ចាស់ៗទាំងអស់រួចរាល់! ឥឡូវអ្នកអាចប្រើ /addattachment ដើម្បីផ្ញើរូបថ្មីចូលបាន។")

@bot.message_handler(commands=['addattachment'])
def ask_attachment(message):
    msg = bot.reply_to(message, "📎 សូមផ្ញើរូបភាព Attachment ចូលមក (អាចផ្ញើច្រើនសន្លឹកដាក់ ២ ជួរ)។ វាយពាក្យ /done ពេលរួចរាល់៖")
    bot.register_next_step_handler(msg, collect_attachments)

def collect_attachments(message):
    chat_id = message.chat.id
    if message.text and message.text.lower() == '/done':
        count = len(user_attachments.get(chat_id, []))
        bot.reply_to(message, f"✅ រក្សាទុក Attachment សរុបចំនួន {count} សន្លឹកជោគជ័យ!")
        return

    if message.photo:
        if chat_id not in user_attachments:
            user_attachments[chat_id] = []
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            img_name = f"attachment_{chat_id}_{len(user_attachments[chat_id])}.jpg"
            with open(img_name, 'wb') as new_file:
                new_file.write(downloaded_file)
                
            user_attachments[chat_id].append(img_name)
            msg = bot.reply_to(message, f"📥 បានទទួល ១ សន្លឹកទៀត (សរុប: {len(user_attachments[chat_id])})។ ផ្ញើបន្ថែម ឬវាយ /done ដើម្បីបញ្ចប់។")
            bot.register_next_step_handler(msg, collect_attachments)
        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា: {e}")
    else:
        msg = bot.reply_to(message, "សូមផ្ញើជារូបភាព ឬវាយ /done ដើម្បីបញ្ចប់។")
        bot.register_next_step_handler(msg, collect_attachments)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = """
សួស្តី! បញ្ជាដែលអ្នកអាចប្រើបាន៖
/invoice - បង្កើតវិក្កយបត្រ A4 (ប្តូររៀលជាដុល្លារ 1$=4000៛)
/settitle - កែប្រែចំណងជើងវិក្កយបត្រ
/setlogo - កែប្រែ Logo
/clearattachment - លុបរូប Attachment ចាស់ចោល
/addattachment - បន្ថែមរូបភាព Attachment ថ្មី (ដាក់ ២ ជួរស្អាត)
    """
    bot.reply_to(message, text)

@bot.message_handler(commands=['invoice'])
def ask_for_items(message):
    text = "សូមបញ្ចូលមុខទំនិញ និងតម្លៃ (អាចបញ្ចូលជាដុល្លារ ឬរៀល)៖\nឧទាហរណ៍៖\nកៅអី - 15$\nតុ - 20000៛"
    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, generate_invoice)

def generate_invoice(message):
    bot.reply_to(message, "កំពុងរៀបចំវិក្កយបត្រ A4 និងจัดតុបតែងរូបភាព... ⏳")
    
    chat_id = message.chat.id
    user_input = message.text
    lines = user_input.split('\n')
    
    table_rows = ""
    total_usd = 0.0
    count = 1
    
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            item_name = parts[0].strip()
            price_str = parts[1].strip().lower()
            
            numbers = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", price_str)
            if numbers:
                val = float(numbers[0])
                final_usd = 0.0
                
                if '៛' in price_str or 'រៀល' in price_str or 'riel' in price_str:
                    final_usd = val / 4000.0
                else:
                    final_usd = val
                
                total_usd += final_usd
                
                table_rows += f"""
                <tr>
                    <td>{count}</td>
                    <td class="text-left">{item_name}</td>
                    <td>1</td>
                    <td></td>
                    <td>$ {final_usd:,.2f}</td>
                    <td>$ {final_usd:,.2f}</td>
                    <td></td>
                </tr>
                """
                count += 1

    logo_path = os.path.abspath("logo.jpg")
    logo_html = f'<img src="file://{logo_path}" class="logo" alt="Logo">' if os.path.exists("logo.jpg") else ''
    
    # យកចំណងជើងដែល User បានកំណត់ (បើគ្មាន ប្រើពាក្យ "បញ្ជីទិញឥវ៉ាន់" ជាលំនាំដើម)
    current_title = user_titles.get(chat_id, "បញ្ជីទិញឥវ៉ាន់")

    # រៀបចំ Attachment ឱ្យដាក់ ២ ជួរ ស្អាតបាត និងមានទំហំសមរម្យ
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
        # បន្ថែមช่องទទេ បើចំនួនរូបសេស ដើម្បីរក្សារចនាសម្ព័ន្ធ ២ ជួរស្មើគ្នា
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
            
            .header-container {{ text-align: center; margin-bottom: 20px; position: relative; height: 80px; }}
            .logo {{ max-height: 80px; max-width: 200px; object-fit: contain; position: absolute; left: 0; top: 0; }}
            h2 {{ color: #000; margin-top: 20px; font-weight: 700; font-size: 20px; text-decoration: underline; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
            th, td {{ border: 1px solid #000; padding: 6px; text-align: center; }}
            th {{ background-color: #f0f0f0; font-weight: 700; }}
            .text-left {{ text-align: left; }}
            .text-right {{ text-align: right; padding-right: 15px; }}
            .total-row td {{ font-weight: bold; background-color: #eef2f5; font-size: 14px; }}
            
            .signatures {{ margin-top: 30px; width: 100%; display: table; }}
            .sig-box {{ display: table-cell; text-align: center; width: 50%; font-weight: bold; }}
            .sig-line {{ margin-top: 60px; }}
            
            /* រចនាសម្ព័ន្ធរូបភាព Attachment ដាក់ ២ ជួរស្អាត និងមានស៊ុមសមរម្យ */
            .attachment-section {{ margin-top: 25px; page-break-inside: avoid; }}
            .attachment-title {{ font-weight: bold; margin-bottom: 8px; text-decoration: underline; font-size: 12px; }}
            .img-table {{ width: 100%; border-collapse: collapse; border: none; }}
            .img-table td {{ border: none; padding: 5px; vertical-align: middle; text-align: center; }}
            .img-cell {{ width: 50%; }}
            .attachment-img {{ max-width: 90%; max-height: 180px; object-fit: contain; border: 1px solid #ccc; padding: 3px; background-color: #fafafa; }}
        </style>
    </head>
    <body>
        <div class="header-container">
            {logo_html}
            <h2>{current_title}</h2>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 5%;">លរ</th>
                    <th style="width: 40%;">បរិយាយ</th>
                    <th style="width: 10%;">បរិមាណ</th>
                    <th style="width: 10%;">ឯកតា</th>
                    <th style="width: 12%;">តម្លៃ ($)</th>
                    <th style="width: 13%;">តម្លៃសរុប ($)</th>
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
            document=('Invoice_A4.pdf', pdf_file),
            caption="វិក្កយបត្រ A4 របស់អ្នករួចរាល់ហើយ! (កែចំណងជើង និងจัดរូប ២ ជួរស្អាត) 🎉"
        )
    except Exception as e:
        bot.reply_to(message, f"សុំទោស! មានបញ្ហាក្នុងការបង្កើត PDF: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_web_server).start()
    print("Bot កំពុងដំណើរការ...")
    bot.infinity_polling()
