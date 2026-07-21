import telebot
from weasyprint import HTML
from flask import Flask
import threading
import os

# ១. ទាញយក Token ពី Environment Variable របស់ Render (ដើម្បីសុវត្ថិភាព)
# ប្រសិនបើវារកមិនឃើញ វានឹងប្រើ Token ដែលអ្នកបានដាក់ (សូមដូរ 'YOUR_BOT_TOKEN_HERE' ផង)
API_TOKEN = os.environ.get('BOT_TOKEN', '8878587093:AAFncmD_3pLSir1paGSUgkzPhNhL4oO40Hg') 
bot = telebot.TeleBot(API_TOKEN)

# ២. បង្កើត Web Server តូចមួយជាមួយ Flask សម្រាប់ឱ្យ UptimeRobot អាច Ping ហៅកុំឱ្យវាដេក
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot កំពុងដំណើរការយ៉ាងរលូន! 🟢"

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ៣. មុខងារ Bot (ឆ្លើយតប និង បង្កើត PDF)
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "សួស្តី! វាយពាក្យ /invoice ដើម្បីសាកល្បងឱ្យខ្ញុំបញ្ចេញវិក្កយបត្រជា PDF។")

@bot.message_handler(commands=['invoice'])
def send_invoice(message):
    bot.reply_to(message, "កំពុងរៀបចំវិក្កយបត្រ សូមរង់ចាំបន្តិច... ⏳")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: sans-serif; padding: 20px; color: #333; }
            h1 { color: #0056b3; text-align: center; border-bottom: 2px solid #0056b3; padding-bottom: 10px; }
            .invoice-box { border: 1px solid #eee; padding: 30px; border-radius: 10px; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f8f9fa; }
            .total { text-align: right; font-weight: bold; font-size: 1.2em; margin-top: 20px; color: #d9534f; }
        </style>
    </head>
    <body>
        <div class="invoice-box">
            <h1>វិក្កយបត្រ (INVOICE)</h1>
            <p><strong>អតិថិជន:</strong> លោក សាមី (Samy)</p>
            <p><strong>កាលបរិច្ឆេទ:</strong> ២១ កក្កដា ២០២៦</p>
            <table>
                <tr><th>បរិយាយ (Description)</th><th>ចំនួន (Qty)</th><th>តម្លៃ (Price)</th><th>សរុប (Total)</th></tr>
                <tr><td>សេវាកម្មរៀបចំ Telegram Bot</td><td>1</td><td>$150.00</td><td>$150.00</td></tr>
            </table>
            <div class="total">សរុបទឹកប្រាក់: $150.00</div>
        </div>
    </body>
    </html>
    """
    try:
        pdf_file = HTML(string=html_content).write_pdf()
        bot.send_document(
            message.chat.id, 
            document=('Invoice_001.pdf', pdf_file),
            caption="នេះគឺជាវិក្កយបត្ររបស់អ្នក! 🎉"
        )
    except Exception as e:
        bot.reply_to(message, f"សុំទោស! មានបញ្ហាក្នុងការបង្កើត PDF: {e}")

# ៤. បញ្ជាឱ្យ Bot និង Web Server ដំណើរការព្រមគ្នា
if __name__ == "__main__":
    # បើក Flask លើ Thread ផ្សេងដើម្បីកុំឱ្យទាក់គ្នាជាមួយ Bot
    threading.Thread(target=run_web_server).start()
    
    print("Bot កំពុងដំណើរការ...")
    bot.infinity_polling()