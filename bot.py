import telebot
from weasyprint import HTML
from flask import Flask
import threading
import os
import re

# ១. ទាញយក Token
API_TOKEN = os.environ.get('BOT_TOKEN', '8878587093:AAFncmD_3pLSir1paGSUgkzPhNhL4oO40Hg') 
bot = telebot.TeleBot(API_TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot កំពុងដំណើរការយ៉ាងរលូន! 🟢"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ២. មុខងារផ្លាស់ប្តូរ Logo
@bot.message_handler(commands=['setlogo'])
def ask_logo(message):
    msg = bot.reply_to(message, "🖼 សូមផ្ញើរូបភាពដែលអ្នកចង់ដាក់ជា Logo (សូមផ្ញើជាទម្រង់រូបភាព/Photo):")
    bot.register_next_step_handler(msg, save_logo)

def save_logo(message):
    if message.photo:
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open("logo.jpg", 'wb') as new_file:
                new_file.write(downloaded_file)
            bot.reply_to(message, "✅ រក្សាទុក Logo ជោគជ័យ! រាល់វិក្កយបត្រថ្មីនឹងប្រើ Logo នេះ។")
        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា: {e}")
    else:
        bot.reply_to(message, "❌ សូមផ្ញើជារូបភាពប៉ុណ្ណោះ។ សូមវាយ /setlogo ម្តងទៀត។")

# ៣. មុខងារផ្លាស់ប្តូរ Attachment
@bot.message_handler(commands=['setattachment'])
def ask_attachment(message):
    msg = bot.reply_to(message, "📎 សូមផ្ញើរូបភាពដែលអ្នកចង់ដាក់ជាឯកសារភ្ជាប់ (Attachment) នៅខាងក្រោម៖")
    bot.register_next_step_handler(msg, save_attachment)

def save_attachment(message):
    if message.photo:
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open("attachment.jpg", 'wb') as new_file:
                new_file.write(downloaded_file)
            bot.reply_to(message, "✅ រក្សាទុក Attachment ជោគជ័យ!")
        except Exception as e:
            bot.reply_to(message, f"❌ មានបញ្ហា: {e}")
    else:
        bot.reply_to(message, "❌ សូមផ្ញើជារូបភាពប៉ុណ្ណោះ។ សូមវាយ /setattachment ម្តងទៀត។")

# ៤. មុខងារស្វាគមន៍ និងបង្កើតវិក្កយបត្រ
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = """
សួស្តី! នេះជាបញ្ជាដែលអ្នកអាចប្រើបាន៖
/invoice - បង្កើតវិក្កយបត្រ
/setlogo - ផ្លាស់ប្តូរ Logo ខាងលើ
/setattachment - ផ្លាស់ប្តូររូបភាពភ្ជាប់ខាងក្រោម
    """
    bot.reply_to(message, text)

@bot.message_handler(commands=['invoice'])
def ask_for_items(message):
    text = "សូមបញ្ចូលមុខទំនិញ និងតម្លៃ (ឈ្មោះទំនិញ - តម្លៃ)៖\nឧទាហរណ៍៖\nINVOICE 01 - 19.25$\nINVOICE 02 - 15.90$"
    msg = bot.reply_to(message, text)
    bot.register_next_step_handler(msg, generate_invoice)

def generate_invoice(message):
    bot.reply_to(message, "កំពុងរៀបចំវិក្កយបត្រ សូមរង់ចាំបន្តិច... ⏳")
    
    user_input = message.text
    lines = user_input.split('\n')
    
    table_rows = ""
    total_usd = 0.0
    count = 1
    
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            item_name = parts[0].strip()
            price_str = parts[1].strip()
            
            numbers = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", price_str)
            if numbers:
                price_val = float(numbers[0])
                total_usd += price_val
                
                table_rows += f"""
                <tr>
                    <td>{count}</td>
                    <td class="text-left">{item_name}</td>
                    <td>1</td>
                    <td></td>
                    <td>$ {price_val:,.2f}</td>
                    <td>$ {price_val:,.2f}</td>
                    <td></td>
                </tr>
                """
                count += 1

    # រៀបចំទីតាំងរូបភាព Logo និង Attachment បើមាន
    logo_path = os.path.abspath("logo.jpg")
    attachment_path = os.path.abspath("attachment.jpg")
    
    logo_html = f'<img src="file://{logo_path}" class="logo" alt="Logo">' if os.path.exists("logo.jpg") else ''
    
    if os.path.exists("attachment.jpg"):
        attachment_html = f"""
        <div class="attachment-section">
            <p class="attachment-title">ឯកសារភ្ជាប់ (Attachment):</p>
            <img src="file://{attachment_path}" class="attachment-img" alt="Attachment">
        </div>
        """
    else:
        attachment_html = ""

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{ size: A4; margin: 15mm; }}
            @import url('https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&display=swap');
            body {{ font-family: 'Battambang', sans-serif; font-size: 13px; color: #000; }}
            
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
            
            .attachment-section {{ margin-top: 40px; text-align: left; page-break-inside: avoid; }}
            .attachment-title {{ font-weight: bold; margin-bottom: 10px; text-decoration: underline; }}
            .attachment-img {{ max-width: 90%; max-height: 300px; border: 1px dashed #ccc; padding: 5px; display: block; margin: 0 auto; }}
        </style>
    </head>
    <body>
        <div class="header-container">
            {logo_html}
            <h2>បញ្ជីទិញឥវ៉ាន់</h2>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 5%;">លរ</th>
                    <th style="width: 40%;">បរិយាយ</th>
                    <th style="width: 10%;">បរិមាណ</th>
                    <th style="width: 10%;">ឯកតា</th>
                    <th style="width: 12%;">តម្លៃ</th>
                    <th style="width: 13%;">តម្លៃសរុប</th>
                    <th style="width: 10%;">ផ្សេងៗ</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
                <tr class="total-row">
                    <td colspan="5" class="text-right">សរុប</td>
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

        {attachment_html}
    </body>
    </html>
    """
    
    try:
        pdf_file = HTML(string=html_content).write_pdf()
        bot.send_document(
            message.chat.id, 
            document=('Invoice.pdf', pdf_file),
            caption="នេះគឺជាវិក្កយបត្ររបស់អ្នក! 🎉"
        )
    except Exception as e:
        bot.reply_to(message, f"សុំទោស! មានបញ្ហាក្នុងការបង្កើត PDF: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_web_server).start()
    print("Bot កំពុងដំណើរការ...")
    bot.infinity_polling()
