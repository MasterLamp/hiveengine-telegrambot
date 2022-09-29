import logging
import re
from hiveengine.wallet import Wallet, Token
from hiveengine.api import Api
import telegram
from telegram import Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handleReply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message.text
    if message == "👍":
        for trade in update.effective_message.reply_to_message.text.split('\n'):
            symbol = None
            amount = None
            pattern = "\\b[A-Z]{2,}"
            x = re.findall(pattern, trade)
            if len(x) == 1:
                symbol = x[0]
            elif x[0] == "SWAP":
                symbol = x[0] + "." + x[1]
            pattern = "[+-]?((\d+(\.\d+)?)|(\.\d+))"
            x = re.findall(pattern, trade)
            if len(x) > 0:
                amount = x[0][0]
            token = Token(symbol)
            marketInfo = token.get_market_info()
            price = None
            text = None
            if "Bought" in trade:
                price = marketInfo.get('lowestAsk')
                text = "Create new SELL order for " + str(amount) + " " + str(symbol) + " @ " + str(price)
            elif "Sold" in trade:
                price = marketInfo.get('highestBid')
                text = "Create new BUY order for " + str(amount) + " " + str(symbol) + " @ " + str(price)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_to_message_id=update.effective_message.message_id)
    elif message == "👎":
        print("Order dismissed.")

async def determinePastTrades(trades, context):
    symbol = "DHEDGE"
    api = Api(url="https://api.primersion.com/")
    w = Wallet("master-lamps", api=api)
    filteredHistory = None
    filter = ["market_sell","market_buy"]
    returnMsgs = []
    if trades != None:
        logging.info(msg="Found trade history for this chat.")
        logMsg = str(len(trades)) + " trades in history."
        logging.info(msg=logMsg)
        history = w.get_history(symbol=[symbol,symbol],limit=1000)
        logMsg = "Retrieved " + str(len(history)) + " from API."
        logging.info(msg=logMsg)
        logMsg = "Filter retrieved trades with trade history"
        logging.info(msg=logMsg)
        filteredHistory = [h for h in history if h.get('transactionId') not in trades and h.get('operation') in filter]
        logMsg = str(len(filteredHistory)) + " new trades filtered."
        logging.info(msg=logMsg)
        filteredTransactionIds = [h.get('transactionId') for h in filteredHistory]
        trades += filteredTransactionIds
        context.chat_data['trades'] = trades
    elif trades == None:
        logMsg = "No trade history for this chat."
        logging.info(msg=logMsg)
        history = w.get_history(symbol=[symbol,symbol],limit=1000)
        logMsg = "Retrieved " + str(len(history)) + " from API."
        logging.info(msg=logMsg)
        transactionIds = [t.get('transactionId') for t in history if t.get('operation') in filter]
        context.chat_data['trades'] += [transactionIds]
    if filteredHistory != None:
        if len(filteredHistory) == 0:
            logMsg = "No new trades to report."
            logging.info(msg=logMsg)
        else:
            logMsg = "Create messages for new trades."
            logging.info(msg=logMsg)
            for trade in filteredHistory:
                if trade.get('operation') == 'market_buy':
                    returnMsg = "Bought <b>" + trade.get('quantityTokens') + " " + trade.get('symbol') + '</b> from ' + trade.get('from')
                    returnMsgs += [returnMsg]
                elif trade.get('operation') == 'market_sell':
                    returnMsg = "Sold <b>" + trade.get('quantityTokens') + " " + trade.get('symbol') + '</b> to ' + trade.get('to')
                    returnMsgs += [returnMsg]
    else:
        logMsg = "Create messages for all trades."
        logging.info(msg=logMsg)
        history = history[100:]
        for trade in history:
            if trade.get('operation') == 'market_buy':
                returnMsg = "Bought <b>" + trade.get('quantityTokens') + " " + trade.get('symbol') + '</b> from ' + trade.get('from')
                returnMsgs += [returnMsg]
            elif trade.get('operation') == 'market_sell':
                returnMsg = "Sold <b>" + trade.get('quantityTokens') + " " + trade.get('symbol') + '</b> to ' + trade.get('to')
                returnMsgs += [returnMsg]
    return returnMsgs

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def startJobPastTrades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job_queue.run_repeating(callback=jobPastTrades, interval=60, data=context, chat_id=update.message.chat_id)

async def jobPastTrades(context: ContextTypes.DEFAULT_TYPE):
    trades = context.chat_data.get('trades')
    if trades == None:
        logMsg = "No trades in cache"
        logging.info(msg=logMsg)
        returnMsgs = await determinePastTrades([], context)    
        if len(returnMsgs) > 0:
            returnMsg = '\n'.join(returnMsgs)
            await context.bot.send_message(chat_id=context._chat_id,
                                text=returnMsg,
                                parse_mode=telegram.constants.ParseMode.HTML)
    else:
        returnMsgs = await determinePastTrades(trades, context)    
        if len(returnMsgs) > 0:
            returnMsg = '\n'.join(returnMsgs)
            await context.bot.send_message(chat_id=context._chat_id,
                                text=returnMsg,
                                parse_mode=telegram.constants.ParseMode.HTML)