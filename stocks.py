#export PATH=$PATH:/Users/henrymiddleton/Documents/Programming/Drivers/

'''
need to record: (optional)
total equity on each date: (open, close)
ranking on each date: (open, close)
cash balance: (open, close)
longs: (open, close)
update previous purchases
track each trade/upkeep:
buy, sell, or keep
date
volume
price per share at trade
symbol/company name
price per share increase since purchase
issue that price is 20 minutes after purchases
so make a list of purchases, then wait 25 minutes and scrape for price
for later comparison, check portfolio against buy price of any previous transactions, if they match, give difference
or: maybe better: add up transactions to see what purchases are?
or: since stocks are only bought and sold en masse, compare current holdings to most recent purchase of that stock (i like this best rn)
'''


import time, datetime, bs4
from yahoo_finance import Share
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#need to install yahoo_finance, selenium, potentially geckodriver and add to path

USERNAME = 'NY6_34_A233'
PASSWORD = 'SRQ12983'
DOWJONES = ['AAPL', 'AXP', 'BA', 'CAT', 'CSCO', 'CVX', 'KO', 'DD', 'XOM', 'GE', 'GS', 'HD', 'IBM', 'INTC', 'JNJ',
            'JPM', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 'PFE', 'PG', 'TRV', 'UNH', 'UTX', 'V', 'VZ', 'WMT', 'DIS']
HOLIDAYS = ['2016-01-01', '2016-01-18', '2016-02-15', '2016-03-25', '2016-05-30',
            '2016-07-04', '2016-09-05', '2016-11-24', '2016-12-25']
PORTFOLIO_ELEMENTS = ['Symbol', 'Position', 'Shares', 'Last Trade Date', 'Net Cost Per Share at Purchase',
                      'Total Net Cost of Purchase', 'Current Share Price', 'Current Value', 'Unrealized Gains/Losses',
                      'Percent Unrealized Gains or Losses']

def get_time():
    return str(datetime.datetime.now())[:-7]

def get_date():
    return get_time()[:10]

def fifty_percent_change(share):
    return round(float(share.get_percent_change_from_50_day_moving_average()[:-1])/100, 6)

def twohundred_percent_change(share):
    return round(float(share.get_percent_change_from_200_day_moving_average()[:-1])/100, 6)

#tells if the market is open on a day
def market_is_open(date):
    #date: 'YYYY-MM-DD'
    day = datetime.date(int(date[0:4]), int(date[5:7]), int(date[8:10])).weekday()
    if day == 5 or day == 6 or date in HOLIDAYS:
        return False
    return True

#provides a summary of the current state of the dow jones
def dow_jones_summary():
    for ticker_symbol in DOWJONES:
        print('%s: %s' % (ticker_symbol, Share(ticker_symbol).get_price()))

class StockBot:
    def __init__(self):
        self.driver = webdriver.Firefox()
        self.log_in()
        self.purchased_pending_pricing = []

    #logs the bot in to the game
    def log_in(self):
        self.driver.get('http://www.smgww.org/login.html')

        username_box = self.driver.find_element_by_name('ACCOUNTNO')
        username_box.clear()
        username_box.send_keys(USERNAME)

        password_box = self.driver.find_element_by_name('USER_PIN')
        password_box.clear()
        password_box.send_keys(PASSWORD)
        password_box.send_keys(Keys.RETURN)

        time.sleep(1)#pause to make sure security id cookie is received before switching page

    #shortcut for filling boxes
    def fill_by_id(self, id, message):
        box = self.driver.find_element_by_id(id)
        time.sleep(.5)#i can't believe this worked again lmao
        box.clear
        box.send_keys(message)

    #shortcut for clicking buttons
    def click_by_id(self, id):
        button = self.driver.find_element_by_id(id)
        button.click()

    #purchases a certain volume of stock
    #buy order (maybe sell too) of <10 crashes
    def move_stock(self, ticker_symbol, share_count, is_buying):
        '''
        constraints:
        buy order must be at least ten shares
        sell order?
        verify ticker_symbol is valid? probably not bc will come from legit database
        '''
        if share_count < 10:
            print('Shares must be moved in volumes of 10 or greater.')
            return 0

        self.driver.get('http://www.smgww.org/enterstock.htm')

        #click buy/sell button
        if is_buying:
            self.click_by_id('rbBuy')
        else:
            self.click_by_id('rbSell')

        #enter ticker symbol
        self.fill_by_id('SymbolName', ticker_symbol)
        #enter volume
        self.fill_by_id('BuySellAmt', str(share_count))
        #preview trade
        self.click_by_id('btnSend')
        #confirm pw

        self.fill_by_id('TradePassword', PASSWORD)
        #finalize trade
        self.click_by_id('btnConfirmTrade')
        #record trade

        time.sleep(.5)#magic

        confirmation = self.driver.find_element_by_id('divFinalTradeResponse').text
        print(confirmation)

        if 'Trade Order Confirmed' in confirmation:#record trade if it went through
            if is_buying == True:
                message = 'Bought %s shares of %s, buy price TBD' % (share_count, ticker_symbol)
                print(message)
                self.purchased_pending_pricing.append(ticker_symbol)
            else:#selling
                message = 'Sold %s shares of %s' % (share_count, ticker_symbol)
                print(message)

    def go_to_page(self, page):#janky but it works
        if page not in self.driver.current_url:
            '''button = self.driver.find_elements_by_xpath("//a[@href=\'"+page+"\']")[0]
            button.click()'''
            self.driver.get('http://www.smgww.org/' + page)
            time.sleep(.5)#allow page to load

    def get_cash(self):
        self.go_to_page('pa.html')
        cash = self.driver.find_element_by_id('dvCashBalance').text
        return float(((cash.split('$')[1]).replace(',', '')).replace(')', ''))#return cash properly formatted as float

    def get_longs(self):
        self.go_to_page('pa.html')
        longs = self.driver.find_element_by_id('dvTotalLongs').text
        return float(((longs.split('$')[1]).replace(',', '')).replace(')', ''))#return longs value properly formatted as float

    def get_equity(self):
        self.go_to_page('pa.html')
        longs = self.driver.find_element_by_id('dvTotalEquity').text
        return float(((longs.split('$')[1]).replace(',', '')).replace(')', ''))#return equity properly formatted as float

    def get_table_entries(self, table):
        body = table.find_element_by_tag_name('tbody')
        rows = body.find_elements_by_class_name('google-visualization-table-tr-odd') + body.find_elements_by_class_name('google-visualization-table-tr-even')
        rows_list_form = []
        for row in rows:
            this_row_list_form = []
            row_elements = row.find_elements_by_tag_name('td')
            for element in row_elements:
                this_row_list_form.append(element.text)
            rows_list_form.append(this_row_list_form)
        return rows_list_form

    def get_transactions(self):
        #dateformat = 'YYYY-MM-DD'
        '''
        scrape all transactions from tnotes.html
        filter for date
        create file if buy, mark end of file if selling
        issue: only get one page of table at a time, 10 trades, likely exceeded by trading:
        gvt-page-numbers has all page buttons, exhaust these
        '''
        self.driver.get('http://www.smgww.org/tnotes.html')
        time.sleep(.5)

        all_transactions = []
        table = self.driver.find_element_by_class_name('google-visualization-table')

        page_numbers = table.find_element_by_class_name('google-visualization-table-page-numbers').find_elements_by_tag_name('a')
        buttons = table.find_element_by_class_name('google-visualization-table-page-numbers')
        num_buttons = len(buttons.find_elements_by_tag_name('a'))

        for num in range(num_buttons):
            #record current page
            for entry in self.get_table_entries(table):
                all_transactions.append(entry)
            #click next
            table.find_element_by_class_name('google-visualization-table-page-next').click()

        return all_transactions

    def get_transactions_by_date(self, date):
        all_transactions = self.get_transactions()
        transactions_today = []
        for transaction in all_transactions:
            if transaction[4][:10] == date[:10]:
                transactions_today.append(transaction)
        return transactions_today



    def get_portfolio(self):
        if not 'ahold.html' in self.driver.current_url:
            self.driver.get('http://www.smgww.org/ahold.html')#works here i think
        time.sleep(1)
        holdings_table = self.driver.find_element_by_class_name('google-visualization-table-table')
        row_entries = self.get_table_entries(holdings_table)
        holdings = []
        for row in row_entries:
            entry = {row[0]: row[2]}
            holdings.append(entry)
        return holdings


    def get_cash_remaining(self, purchases, starting_cash):
        cash_used = 0#total cash used
        for stock in purchases:
            cash_used += purchases[stock]*float(Share(stock).get_price())
        cash_remaining = starting_cash - cash_used
        return cash_remaining

    def get_ranking(self):
        self.go_to_page('pa.html')
        rank = self.driver.find_element_by_id('lnkCoordinator').text
        return rank

    def sell_all(self):
        portfolio = self.get_portfolio()
        simple_holdings = {}
        for holding in portfolio:
            simple_holdings[holding['Symbol']] = holding['Shares']
        #working up to here
        for symbol in simple_holdings:
            self.move_stock(symbol, int(simple_holdings[symbol]), 0)#0 means sell

    def buy_below_mean(self, cash):
        to_buy = {}
        for symbol in DOWJONES:
            stock = Share(symbol)
            if fifty_percent_change(stock) < 0:#if price is below the fifty day average
                to_buy[symbol] = stock.get_price()


        cash_per_stock = cash/len(to_buy)
        purchases = {}

        for stock in to_buy:
            share = Share(stock)
            num_to_buy = int(cash_per_stock/float(share.get_price()))
            if num_to_buy < 10:
                to_buy.remove(stock)#must buy at least ten, so wipe from list
            else:
                purchases[stock] = num_to_buy

        cash_remaining = self.get_cash_remaining(purchases, cash)

        while cash_remaining > 10000:#10k dollars, >90% is reasonably well used
            for stock in purchases:
                if cash_remaining - float(Share(stock).get_price()) > 0:#if can afford a single share
                    cash_remaining -= float(Share(stock).get_price())
                    purchases[stock] += 1#mark stock for purchasing an extra share

        return purchases#{symbol: num shares}

    def initiate(self):
        #self.sell_all()
        purchases = self.buy_below_mean(self.get_cash())
        for symbol in purchases:
            self.move_stock(symbol, purchases[symbol], True)
        if str(input('Wait and record stocks now? (y/n)')).lower() == 'y':
                time.sleep(1500)#wait 25 minutes
                self.log_purchases(get_date())
        else:
            print('Make sure to log the purchases later.')



        #wait 25 mins, record prices from get_transactions
        #or maybe get transactions from most recent day and do those stats so no 25 minute wait

    def log_purchases(self, date):
        transactions = self.get_transactions_by_date(date)#get today's (or custom's) transactions
        for transaction in transactions:
            symbol = transaction[1]
            count = transaction[2]
            price = transaction[6].split('$')[1]
            message = 'Bought %s shares of %s at a net cost of %s per share' % (count, symbol, price)
            print(message)
            with open(('purchases/%s_%s.txt' % (date, symbol)), 'w') as log:
                log.write(message)

    def daily_stats(self):
        message = get_date() + ''': Equity: %s Ranking: %s Cash: %s Longs: %s''' % (self.get_equity(), self.get_ranking(), self.get_cash(), self.get_longs())
        print(message)
        with open('dailylog.txt', 'a') as log:
            log.write('\n'+message)


    def maintain(self):
        portfolio = self.get_portfolio()#{symbol: num shares}
        print('got portfolio')
        to_sell = {}
        liquidation_profit = 0#idk if you can spend cash you will have but don't yet

        for entry in portfolio:
            #{symbol: value}
            #hackish but
            for key in entry:
                symbol = key
            share_count = int(entry[symbol])
            stock = Share(symbol)

            print('Created share for %s' % symbol)
            if fifty_percent_change(stock) > 0:#if price is above the fifty day average, sell it
                print('Should sell %s' % symbol)
                price = float(stock.get_price())
                to_sell[symbol] = share_count
                liquidation_profit += price*share_count


        if len(to_sell) > 0:
            print('Stocks to sell: %s' % to_sell)
        else:
            print('No changes.')

        #sell Stocks
        for stock in to_sell:
            self.move_stock(stock, to_sell[stock], 0)#0 means sell
            print('Sold %s shares of %s at %s per share' % (to_sell[stock], stock, Share(stock).get_price()))

        return self.buy_below_mean(liquidation_profit)

    def update_stocks(self, stocks_to_update, original_date):
        for stock in stocks_to_update:
            share = Share(stock)
            file_name = original_date+'_'+stock+'.txt'
            with open('purchases/%s' % file_name, 'a') as log:
                log.write('\n' + get_date()+'Keeping %s at %s' % (stock, share.get_price()))
