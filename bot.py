import telebot
from weasyprint import HTML
from flask import Flask
import threading
import os
import re

# ១. ទាញយក Token
API_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE') 
bot = telebot.TeleBot(API_TOKEN)

# ២. Web Server សម្រាប់ UptimeRobot
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot កំពុងដំណើរការយ៉ាងរលូន! 🟢"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ៣. មុខងារ Bot ឆ្លើយតប
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "សួស្តី! សូមវាយពាក្យ /invoice ដើម្បីចាប់ផ្តើមបង្កើតវិក្កយបត្រ។")

@bot.message_handler(commands=['invoice'])
def ask_for_items(message):
    text = """
សូមបញ្ចូលមុខទំនិញ និងតម្លៃរបស់អ្នក (មួយមុខក្នុងមួយបន្ទាត់)។
ទម្រង់៖ ឈ្មោះទំនិញ - តម្លៃ

ឧទាហរណ៍៖
សេវាកម្ម Telegram Bot - 150$
កូកាកូឡា - 2000៛
ការ៉េម - 1.5$
    """
    msg = bot.reply_to(message, text)
    # ប្រាប់ Bot ឱ្យរង់ចាំទទួលសារបន្ទាប់ពីអ្នកប្រើប្រាស់ រួចបញ្ជូនទៅកាន់មុខងារ generate_invoice
    bot.register_next_step_handler(msg, generate_invoice)

def generate_invoice(message):
    bot.reply_to(message, "កំពុងរៀបចំវិក្កយបត្រ និងគណនាទឹកប្រាក់ សូមរង់ចាំបន្តិច... ⏳")
    
    user_input = message.text
    lines = user_input.split('\n')
    
    table_rows = ""
    total_usd = 0.0
    total_khr = 0
    
    # វដ្ត (Loop) ដើម្បីទាញយកទិន្នន័យពីគ្រប់បន្ទាត់ដែលអ្នកបានវាយបញ្ចូល
    for line in lines:
        if '-' in line:
            parts = line.split('-', 1)
            item_name = parts[0].strip()
            price_str = parts[1].strip()
            
            # ទាញយកតួលេខចេញពីអក្សរ ដើម្បីយកមកបូក
            numbers = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", price_str)
            if numbers:
                price_val = float(numbers[0])
                if '$' in price_str or 'usd' in price_str.lower():
                    total_usd += price_val
                elif '៛' in price_str or 'r' in price_str.lower() or 'រៀល' in price_str:
                    total_khr += int(price_val)
            
            table_rows += f"<tr><td>{item_name}</td><td>1</td><td>{price_str}</td><td>{price_str}</td></tr>"

    # បង្កើតទម្រង់ HTML ដោយប្រើពុម្ពអក្សរខ្មែរ (Battambang) ពី Google Fonts
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Battambang:wght@400;700&display=swap');
            body {{ font-family: 'Battambang', sans-serif; padding: 20px; color: #333; }}
            h1 {{ color: #0056b3; text-align: center; border-bottom: 2px solid #0056b3; padding-bottom: 10px; font-weight: 700;}}
            .invoice-box {{ border: 1px solid #eee; padding: 30px; border-radius: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f8f9fa; font-weight: 700; }}
            .total-box {{ margin-top: 20px; text-align: right; font-size: 1.1em; }}
            .grand-total {{ font-weight: bold; font-size: 1.3em; color: #d9534f; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="invoice-box">
            <h1>វិក្កយបត្រ (INVOICE)</h1>
            <p><strong>អតិថិជន:</strong> ភ្ញៀវទូទៅ</p>
            
            <table>
                <tr>
                    <th>បរិយាយ (Description)</th>
                    <th>ចំនួន (Qty)</th>
                    <th>តម្លៃ (Price)</th>
                    <th>សរុប (Total)</th>
                </tr>
                {table_rows}
            </table>
            
            <div class="total-box">
                <p>សរុប (USD): <strong>${total_usd:,.2f}</strong></p>
                <p>សរុប (KHR): <strong>{total_khr:,} ៛</strong></p>
            </div>
            <p style="text-align: center; margin-top: 50px; font-size: 0.9em; color: #777;">
                សូមអរគុណសម្រាប់ការគាំទ្រសេវាកម្មរបស់យើង!
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        # បំប្លែងទៅជា PDF រួចផ្ញើ
        pdf_file = HTML(string=html_content).write_pdf()
        bot.send_document(
            message.chat.id, 
            document=('Invoice_Auto.pdf', pdf_file),
            caption="នេះគឺជាវិក្កយបត្ររបស់អ្នក! 🎉\n(គណនាដោយស្វ័យប្រវត្តិ)"
        )
    except Exception as e:
        bot.reply_to(message, f"សុំទោស! មានបញ្ហាក្នុងការបង្កើត PDF: {e}")

# ៤. បញ្ជាឱ្យ Bot ដំណើរការ
if __name__ == "__main__":
    threading.Thread(target=run_web_server).start()
    print("Bot កំពុងដំណើរការ...")
    bot.infinity_polling()
