from flask import Blueprint, render_template, request, current_app as app
from Mongo.extensions import mongo
from datetime import datetime
import schedule
import time
import ccxt

# --------------

BTC = Blueprint('BTC', __name__)

# --------------

lockThisFunction = False

# --- Sin uso por el momento, anteriormente servia como limite de perdida y limite de ganancia ---
@BTC.route('/Price-BTC', methods=['POST'])
def Price():
	@app.after_response
	def afterPrice():
		operationFilter = {"Operation-BTC": True}	
		status = mongo.db.Status
		Operation = status.find_one(operationFilter)

		if Operation['status'] == True:
			#getUsers_check()
			pass
		else:
			print("\n --- Price not in Operation --- \n")

	return 'Precio Actualizado'

# --- Define la direccion y los parametros de las operaciones ---
@BTC.route('/Script-BTC', methods=['POST'])
def script():
	status = mongo.db.Status
	scriptJson = request.json
	@app.after_response
	def afterSar():
		operationFilter = {"Operation-BTC": True}	
		Operation = status.find_one(operationFilter)

		if scriptJson['side'] == "BUY":
			
			print("\n --- Order -> " + str(scriptJson['side']) + " --- ")

			if Operation['status'] == True:
				if Operation['side'] == "BUY":
					pass
				else:
					getUsers_cancel()
					orderPrice = scriptJson['close']
					status.update_one(
						{"Operation-BTC": True},
						{"$set": {"status": True, "side": "BUY", "entryPrice": orderPrice}})
					getUsers_create()
			else:
				orderPrice = scriptJson['close']
				status.update_one(
					{"Operation-BTC": True},
					{"$set": {"status": True, "side": "BUY", "entryPrice": orderPrice}})
				getUsers_create()


		elif scriptJson['side'] == "SELL":

			print("\n --- Order -> " + str(scriptJson['side']) + " --- ")

			if Operation['status'] == True:
				if Operation['side'] == "SELL":
					pass
				else:
					getUsers_cancel()
					orderPrice = scriptJson['close']
					status.update_one(
						{"Operation-BTC": True},
						{"$set": {"status": True, "side": "SELL", "entryPrice": orderPrice}})
					getUsers_create()
			else:
				orderPrice = scriptJson['close']
				status.update_one(
					{"Operation-BTC": True},
					{"$set": {"status": True, "side": "SELL", "entryPrice": orderPrice}})
				getUsers_create()	


		else:
			print("Error Request")

	return 'Operacion Realizada'




# --- Crea Operaciones en base a los parametros ---
def getUsers_create():
	global lockThisFunction, thisBot
	if lockThisFunction == True:
		time.sleep(2)
		getUsers_create()
	lockThisFunction = True

	print("\n-------------------- Create -------------------- ")

	bots = mongo.db.Bots
	pairFormat = {"pair": "BTCUSDT"}
	thisPairBot = bots.find(pairFormat)
	for thisBot in thisPairBot:
		if thisBot['isEnabled'] == True and thisBot['isEnabledforTrade'] == True:
			createOrders()
		else:
			pass

	print("\n-------------------- Create -------------------- ")
	lockThisFunction = False
	
def createOrders():
	global issues, tradeAmount
	issues = ""
	import time
	operationFilter = {"Operation-BTC": True}	
	status = mongo.db.Status
	Operation = status.find_one(operationFilter)
	

	#-------------------- BINANCE -------------------- 
	if thisBot['exchange'] == "Binance":
		binance = ccxt.binance({
			'apiKey': (thisBot['exchangeConnection']['apiKey']),
			'secret': (thisBot['exchangeConnection']['apiSecret']),
			'options': {'defaultType': 'future',},})
		
		binance.enableRateLimit = True
		binance.set_leverage(thisBot['quantityLeverage'], 'BTC/BUSD', params={"marginMode": "isolated"})

		def createLimitOrderBinance():
			operationFilter = {"Operation-BTC": True}	
			status = mongo.db.Status
			Operation = status.find_one(operationFilter)
			
			global order, issues, tradeAmount
			retrying = False
			thisOrder = False

			ticker = binance.fetch_ticker('BTC/BUSD')
			orderPrice1 = float(ticker['close'])
			orderPrice = orderPrice1
			tradeAmount = ( ( thisBot['tradeAmount'] * thisBot['quantityLeverage'] ) / orderPrice )

			print("\n -- New Order Price: " + str(orderPrice) + " -- ")

			try:
				if Operation['side'] == "BUY":
					order = binance.create_limit_buy_order('BTC/BUSD', tradeAmount, orderPrice)
					thisOrder = True
				elif Operation['side'] == "SELL":
					order = binance.create_limit_sell_order('BTC/BUSD', tradeAmount, orderPrice)
					thisOrder = True
				else:
					print("ERROR SIDE (SIDE NO DECLARADA) [EXCHANGE]")
			except:
				if retrying == True:
					issues = "None"
					retrying = False
					thisOrder = False
				else:
					issues = "Insufficients founds"
					thisOrder = False
			
			
			time.sleep(3)
			if (thisOrder == True) and (order['status'] == "open"):
				print("\n -- Order Status: Open // Creating Limit Order...-- ")
				retrying = True
				thisOrder = False
				binance.cancel_all_orders('BTC/BUSD')
				createLimitOrderBinance()
			else:
				print("\n -- Order Status: Close -- ")


		createLimitOrderBinance()
		
	
	#-------------------- BYBIT --------------------
	elif thisBot['exchange'] == "Bybit":
		bybit = ccxt.bybit({
			'apiKey': (thisBot['exchangeConnection']['apiKey']),
			'secret': (thisBot['exchangeConnection']['apiSecret']),
			'options': {'defaultType': 'future',},})
		
		bybit.enableRateLimit = True
		bybit.set_leverage(thisBot['quantityLeverage'], 'BTC/BUSD', params={"marginMode": "isolated"})

		def createLimitOrderBybit():
			operationFilter = {"Operation-BTC": True}	
			status = mongo.db.Status
			Operation = status.find_one(operationFilter)
			
			global order, issues, tradeAmount
			retrying = False
			thisOrder = False

			ticker = bybit.fetch_ticker('BTC/BUSD')
			orderPrice1 = float(ticker['close'])
			orderPrice = orderPrice1
			tradeAmount = ( ( thisBot['tradeAmount'] * thisBot['quantityLeverage'] ) / orderPrice )

			print("\n -- New Order Price: " + str(orderPrice) + " -- ")

			try:
				if Operation['side'] == "BUY":
					order = bybit.create_limit_buy_order('BTC/BUSD', tradeAmount, orderPrice)
					thisOrder = True
				elif Operation['side'] == "SELL":
					order = bybit.create_limit_sell_order('BTC/BUSD', tradeAmount, orderPrice)
					thisOrder = True
				else:
					print("ERROR SIDE (SIDE NO DECLARADA) [EXCHANGE]")
			except:
				if retrying == True:
					issues = "None"
					retrying = False
					thisOrder = False
				else:
					issues = "Insufficients founds"
					thisOrder = False
			
			
			time.sleep(3)
			if (thisOrder == True) and (order['status'] == "open"):
				print("\n -- Order Status: Open // Creating Limit Order...-- ")
				retrying = True
				thisOrder = False
				bybit.cancel_all_orders('BTC/BUSD')
				createLimitOrderBybit()
			else:
				print("\n -- Order Status: Close -- ")


		createLimitOrderBybit()
	
	else:
		print("ERROR EN BASE DE DATOS (EXCHANGE INVALIDO)")	
		issues = "Invalid Exchange"
		
	bots = mongo.db.Bots	
	bots.update_one(
		{"_id": thisBot['_id']},
		{"$set": {"lastOrderAmount": tradeAmount}})

	dateTime = datetime.now()
	date = dateTime.strftime("%d/%m/%y")
	ctime = dateTime.strftime("%H:%M:%S")
	bots.update(
		{"_id": thisBot['_id']},
		{"$push": 
			{"log":
		{
			"status": "Open", "side": Operation['side'], "dateOpen": date, "timeOpen": ctime, "dateClose": "-", "timeClose": "-", "amount": tradeAmount, "issuesOpen": issues, "issuesClose": "-"
		}}})





# --- Cancela Operaciones en base a los parametros ---
def getUsers_cancel():
	global lockThisFunction, thisBot
	if lockThisFunction == True:
		time.sleep(2)
		getUsers_cancel()
	lockThisFunction = True
	print("\n-------------------- CANCEL -------------------- ")
	global thisBot
	bots = mongo.db.Bots
	operation = mongo.db.Status
	pairFormat = {"pair": "BTCUSDT",}
	thisPairBot = bots.find(pairFormat)

	for thisBot in thisPairBot:
		if thisBot['isEnabled'] == True and thisBot['isEnabledforTrade'] == True:
			cancelOrders()
		else:
			pass

	operation.update_one(
		{"Operation-BTC": True},
		{"$set": {"status": False, "side": "", "entryPrice": 0.00}})
	lockThisFunction = False
	print("\n-------------------- CANCEL -------------------- ")

def cancelOrders():
	global issues
	issues = ""
	import time
	operationFilter = {"Operation-BTC": True}	
	status = mongo.db.Status
	Operation = status.find_one(operationFilter)
	
	#-------------------- BINANCE -------------------- 
	if thisBot['exchange'] == "Binance":
		binance = ccxt.binance({
			'apiKey': (thisBot['exchangeConnection']['apiKey']),
			'secret': (thisBot['exchangeConnection']['apiSecret']),
			'options': {'defaultType': 'future',},})
		
		binance.enableRateLimit = True
		
		def createMarketOrderBinance():
			operationFilter = {"Operation-BTC": True}	
			status = mongo.db.Status
			Operation = status.find_one(operationFilter)
			
			global order, issues

			orderTime1 = time.localtime()
			orderTime = str(orderTime1.tm_min) + str(orderTime1.tm_sec)

			try:
				if Operation['side'] == "BUY":
					order = binance.create_market_sell_order('BTC/BUSD', thisBot['lastOrderAmount'], params={'reduce_only': True})
					issues = "None"
				elif Operation['side'] == "SELL":
					order = binance.create_market_buy_order('BTC/BUSD', thisBot['lastOrderAmount'], params={'reduce_only': True})
					issues = "None"
				else:
					print("ERROR SIDE (SIDE NO DECLARADA) [EXCHANGE]")
					issues = "Invalid data"
			except:
				issues = "No order Open"
			


		createMarketOrderBinance()
	
	#-------------------- BYBIT --------------------
	elif thisBot['exchange'] == "Bybit":
		bybit = ccxt.bybit({
			'apiKey': (thisBot['exchangeConnection']['apiKey']),
			'secret': (thisBot['exchangeConnection']['apiSecret']),
			'options': {'defaultType': 'future',},})
		
		bybit.enableRateLimit = True
		
		def createMarketOrderBybit():
			operationFilter = {"Operation-BTC": True}	
			status = mongo.db.Status
			Operation = status.find_one(operationFilter)
			
			global order, issues

			orderTime1 = time.localtime()
			orderTime = str(orderTime1.tm_min) + str(orderTime1.tm_sec)

			try:
				if Operation['side'] == "BUY":
					order = bybit.create_market_sell_order('BTC/BUSD', thisBot['lastOrderAmount'], params={'reduce_only': True})
					issues = "None"
				elif Operation['side'] == "SELL":
					order = bybit.create_market_buy_order('BTC/BUSD', thisBot['lastOrderAmount'], params={'reduce_only': True})
					issues = "None"
				else:
					print("ERROR SIDE (SIDE NO DECLARADA) [EXCHANGE]")
					issues = "Invalid data"
			except:
				issues = "No order Open"


		createMarketOrderBybit()
	
	else:
		print("ERROR EN BASE DE DATOS (EXCHANGE INVALIDO)")	
		issues = "Data Error (Report with Admins)"

	bots = mongo.db.Bots
	dateTime = datetime.now()
	date = dateTime.strftime("%d/%m/%y")
	ctime = dateTime.strftime("%H:%M:%S")
	bots.update_one(
		{"_id": (thisBot['_id']), "log.status": "Open"},
		{"$set": {"log.$.status": "Close", "log.$.dateClose": date, "log.$.timeClose": ctime, "log.$.issuesClose": issues}})











# --- Actualiza cada 24hrs la base de datos de usuarios en base a los parametros ---
def getUsers_update():
	global lockThisFunction, thisBot
	if lockThisFunction == True:
		time.sleep(2)
		getUsers_update()
	lockThisFunction = True

	operationFilter = {"Operation-BTC": True}	
	status = mongo.db.Status
	Operation = status.find_one(operationFilter)

	if Operation['status'] == True:

		status.update_one(
			{"Operation-BTC": True},
			{"$set": {"updatePending": True}})

	else:

		global thisBot
		bots = mongo.db.Bots
		pairFormat = {"pair": "BTCUSDT",}
		thisPairBot = bots.find(pairFormat)

		for thisBot in thisPairBot:
			if thisBot['isEnabled'] == True:
				updateBots()
			else:
				pass

def updateBots():
	#-------------------- BINANCE -------------------- 
	if thisBot['exchange'] == "Binance":
		binance = ccxt.binance({
			'apiKey': (thisBot['exchangeConnection']['apiKey']),
			'secret': (thisBot['exchangeConnection']['apiSecret']),
			'options': {'defaultType': 'future',},})
		
		binance.enableRateLimit = True
		
		balance = binance.fetch_balance()
		balanceBUSD = balance['BUSD']['total']
		newTradeAmount = balanceBUSD * .75

		if thisBot['isEnabled'] == True:
			bots = mongo.db.Bots	
			bots.update_one(
				{"_id": thisBot['_id']},
				{"$set": {"tradeAmount": newTradeAmount, "isEnabledforTrade": True}})

		else:
			print("Bot Disabled")
	
	#-------------------- BYBIT --------------------
	elif thisBot['exchange'] == "Bybit":
		bybit = ccxt.binance({
			'apiKey': (thisBot['exchangeConnection']['apiKey']),
			'secret': (thisBot['exchangeConnection']['apiSecret']),
			'options': {'defaultType': 'future',},})
		
		bybit.enableRateLimit = True
		
		balance = bybit.fetch_balance()
		balanceBUSD = balance['BUSD']['total']
		newTradeAmount = balanceBUSD * .75

		if thisBot['isEnabled'] == True:
			bots = mongo.db.Bots	
			bots.update_one(
				{"_id": thisBot['_id']},
				{"$set": {"tradeAmount": newTradeAmount, "isEnabledforTrade": True}})

		else:
			print("Bot Disabled")


@BTC.route('/BTC', methods=['GET'])
def btc():
	binance = ccxt.binance({
		'apiKey': 'hJkAG2ynUNlMRGn62ihJh5UgKpZKk6U2wu0BXmKTvlZ5VBATNd1SRdAN43q9Jtaq',
		'secret': '3b7qmlRibSsbnLQhHIoOFogqROqr9FXxg563nyRj5pjJsvcJWpFnxyggA5TaTyfJ',
		'options': {'defaultType': 'future',},})
	binance.enableRateLimit = True
	ticker = binance.fetch_ticker('BTC/BUSD')
	price = float(ticker['close'])
	status = mongo.db.Status

	squeezeFilter = {"Squeeze-BTC": True}
	sqzmomFilter = {"SQZMOM-BTC": True}
	hullFilter = {"Hull-BTC": True}
	sarFilter = {"Sar-BTC": True}
	operationFilter = {"Operation-BTC": True}

	SqueezeS = status.find_one(squeezeFilter)
	SqzmomS = status.find_one(sqzmomFilter)
	HullS = status.find_one(hullFilter)
	SarS = status.find_one(sarFilter)
	OperationS = status.find_one(operationFilter)

	Squeeze = SqueezeS['status']
	Sqzmom = SqzmomS['status']
	Hull = HullS['status']
	Sar = SarS['status']
	Operation = OperationS['status']
	Side = OperationS['side']
	StopL = OperationS['stopLoss']
	EntryP = OperationS['entryPrice']
	
	if Squeeze == "ON": SqueezeColor = "primary"
	else: SqueezeColor = "secondary"
	if Sqzmom == "BUY IMPULSE": SqzmomColor = "success"
	elif Sqzmom == "BUY MOVEMENT": SqzmomColor = "success"
	elif Sqzmom == "SELL MOVEMENT": SqzmomColor = "danger"
	else: SqzmomColor = "danger"
	if Hull == "BUY": HullColor = "success"
	else: HullColor = "danger"
	if Sar == "BUY": SarColor = "success"
	else: SarColor = "danger"
	if Operation == True: OperationColor = "primary"
	else: OperationColor = "secondary"
	if StopL == 0.00: slColor = "secondary"
	else: slColor = "primary"
	if Side == "BUY": SideColor = "success"
	elif Side == "SELL": SideColor = "danger"
	else: SideColor = "secondary"
	if EntryP == 0: epColor = "secondary"
	else: epColor = "primary"
	
	return render_template('bitcoin.html', 
	Squeeze=Squeeze,
	Sqzmom=Sqzmom,
	Hull=Hull,  
	Sar=Sar, 
	Operation=Operation,
	StopL=StopL,
	SqueezeColor=SqueezeColor,
	SqzmomColor=SqzmomColor,
	HullColor=HullColor,
	SarColor=SarColor,
	OperationColor=OperationColor,
	slColor=slColor,
	Price=price,
	Side=Side,
	SideColor=SideColor,
	EntryP=EntryP,
	epColor=epColor)



#schedule.every(6).seconds.do(getUsers_check)
schedule.every().day.at("00:00").do(getUsers_update)

while 1==1:
	schedule.run_pending()
	time.sleep(6)
