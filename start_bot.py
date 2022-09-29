import os
from telegram.ext import CommandHandler, Application, PicklePersistence

import hiveenginetelegram
 
pickleFile = PicklePersistence("hiveenginebot-data.pickle")

application = Application.builder().token(os.environ['HIVEENGINE_TELEGRAM_API_KEY']).persistence(persistence=pickleFile).build()
jobPastTrades_handler = CommandHandler('startJobPastTrades', hiveenginetelegram.startJobPastTrades)
application.add_handler(jobPastTrades_handler)
application.run_polling()