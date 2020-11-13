class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ETH-USDT'],
            },
        }

        # 60 sec
        self.period = 10 * 60
        self.options = {}

        # user defined class attribute
        self.last_type = 'sell'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 10
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2


    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN


    # called every self.period
    def trade(self, information):

        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        close_price = information['candles'][exchange][pair][0]['close']
        open_price = information['candles'][exchange][pair][0]['open']
        high_price = information['candles'][exchange][pair][0]['high']
        low_price = information['candles'][exchange][pair][0]['low']
        volume = information['candles'][exchange][pair][0]['volume']


        targetCurrency = pair.split('-')[0]  #BTC
        baseCurrency = pair.split('-')[1]  #USDT
        
        baseCurrency_amount = self['assets'][exchange][baseCurrency] 
        targetCurrency_amount = self['assets'][exchange][targetCurrency] 

        # add latest price into trace
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()

        Log('info: ' + str(information['candles'][exchange][pair][0]['time']) + ', ' + str(information['candles'][exchange][pair][0]['open']) + ', assets' + str(self['assets'][exchange]['ETH']))

        if cur_cross is None:
            return []

        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []

        if baseCurrency_amount < 2000:
            return []

        fastk, fastd = talib.STOCHRSI(self.close_price_trace, timeperiod=14, fastk_period=5, fastd_period=3, fastd_matype=0)
        if fastk[-1] > 80:
            return [
                {
                    'exchange': exchange,
                    'amount': 1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif fastk[-1] < 20:
            return [
                {
                    'exchange': exchange,
                    'amount': -1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        
        # cross up
        if self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying, opt1:' + self['opt1'])
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        # cross down
        elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('selling, ' + exchange + ':' + pair)
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -1,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross
        return []
