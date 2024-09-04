from lumibot.brokers import Alpaca # will act as the broker
from lumibot.backtesting import YahooDataBacktesting # will give the framework for backtesting
from lumibot.strategies.strategy import Strategy # will be the trading bot
from lumibot.traders import Trader # gives ability to deploy it live
from datetime import datetime # self explanatory
from alpaca_trade_api import REST #allows to dynamically take high volume of data from Alpaca API
from timedelta import Timedelta
from finbert1_util import estimate_sentiment
#make an Alpaca Account and fill the details below

BASE_URL = ""
API_KEY = ""
API_SECRET = ""

# need to traverse a dictionary to Alpaca Broker

Alpaca_Credits = {
    "API_KEY": API_KEY, #setting the dictionary key to apiKey
    "API_SECRET": API_SECRET,
    "PAPER_TRADING": True # will NOT be using real cash!

}

#create a new framework for strategy
#will form the backbone to our trading bot
#all trading logic goes here
class ML_Trader(Strategy):

    
    #Life Cycle Methods:
        #1. Init function runs once
        #2. The on trading iteration runs every time new data is collected
    
   

    def initialize(self, symbol:str="SPY", cash_at_risk: float=.5):
        self.symbol = symbol
        #how frequently you'll trade
        self.sleeptime = "17H" #change if you'd like
        self.last_trade = None # no trade before this one
        self.cash_at_risk = cash_at_risk
        self.api = REST(base_url=BASE_URL,key_id=API_KEY, secret_key=API_SECRET )

    def get_dates(self):
        today = self.get_datetime()
        three_day_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_day_prior.strftime('%Y-%m-%d')
    
    #now implementing the ML aspect, using News 
    def get_sentiment1(self):
       today, three_days_prior = self.get_dates()
       news = self.api.get_news(symbol=self.symbol, 
                                start=three_days_prior, 
                                end=today ) #news for 3 days
       #processing news
       news = [evnt.__dict__["_raw"]["headline"]for evnt in news]
       probability, sentiment = estimate_sentiment(news)
       return probability, sentiment


    #instead of randomly buying 10, make it better and dynamic
    def position_size(self):
        #remaining money
        cash_left = self.get_cash()
        last_price = self.get_last_price(self.symbol)

    #position size will be calculated based on a metric called cash a risk
    # is is how much of the cash can we risk at every trade
        quantity = round(cash_left * self.cash_at_risk / last_price,0) # tells us how many units we get per amount we want to risk
        return cash_left, last_price, quantity


    
    def on_trading_iteration(self):
        #creating a base trade
        cash_left, last_price, quantity = self.position_size()
        probability, sentiment  = self.get_sentiment1()

        if cash_left > last_price:
                if sentiment=="positive" and probability>.999:
                    if self.last_order=="sell":
                        self.sell_all()
                    #new order will have params like what symbol you want to but and how many of those you want
                    new_order = self.create_order(
                                              self.symbol, 
                                              quantity, "buy", 
                                              type="bracket", 
                                              take_profit_price=last_price*1.20,# we want it to go up by 20 percent for sufficient take profits)
                                              stop_loss_price = last_price * .95
                    )
                    #now set a take profit (starts a trade that sets a bound,if it hits that point then we automatically sell ) and stop loss
                    #update order
                    self.submit_order(new_order)
                    self.last_trade = "buy"

                elif sentiment=="negative" and probability>.999:
                    if self.last_order=="buy":
                        self.sell_all()
                    #new order will have params like what symbol you want to but and how many of those you want
                    new_order = self.create_order(
                                              self.symbol, 
                                              quantity, "sell", 
                                              type="bracket", 
                                              take_profit_price=last_price*0.8,# we want it to go up by 20 percent for sufficient take profits)
                                              stop_loss_price = last_price * 1.05
                    )
                    #now set a take profit (starts a trade that sets a bound,if it hits that point then we automatically sell ) and stop loss
                    #update order
                    self.submit_order(new_order)
                    self.last_trade = "sell"

broker = Alpaca(Alpaca_Credits)
#leave parameters as a blank dictionary for now
strategy = ML_Trader(name='ml_strategy', broker=broker, parameters={"symbol":"SPY",
                                                                    "cash_at_risk":.5})


#Set start date and end date for the yahoo data
#Use the datetime library

start_date = datetime(2024, 1,1)# change to your liking Y/M/D
end_date = datetime(2024,7,7)


strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol": "SPY", "cash_at_risk":.5}# can change cash at risk depending on how risky the bot should be
)
