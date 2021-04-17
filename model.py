class PortfolioState:
    def __init__(self):
        self.date = None
        self.positions = {}  # coin to Position

    def add_trade(self, flow_event):
        if self.date is None or flow_event.date > self.date:
            self.date = flow_event.date
        coin = flow_event.buy_asset
        buy_currency = flow_event.sell_asset
        if coin not in self.positions:
            self.positions[coin] = Position(coin, buy_currency)
        self.positions[coin].update_position(flow_event)

    def __str__(self):
        output = f"Portfolio state on {self.date}\n"
        for coin in self.positions:
            output += f"{str(self.positions[coin])}\n"
        return output


class Position:
    def __init__(self, asset_name, buy_currency):
        self.asset_name = asset_name
        self.buy_currency = buy_currency
        self.volume = 0
        self.buy_price = None

    # TODO: Must be able to make a position smaller or close it.
    def update_position(self, flow_event):
        print("Update position")
        print(flow_event)
        self.__check_valid(flow_event)
        new_volume = flow_event.buy_volume
        new_price = flow_event.unit_price
        if self.volume == 0:
            self.buy_price = new_price
            self.volume = new_volume
        else:
            self.buy_price = (self.buy_price * self.volume +
                              new_price * new_volume) / (self.volume + new_volume)
            self.volume += new_volume

    def __check_valid(self, flow_event):
        if self.asset_name != flow_event.buy_asset:
            raise Exception(
                f"This position is {self.asset_name} not {flow_event.buy_asset}")
        if self.buy_currency != flow_event.sell_asset:
            raise Exception(
                f"{self.asset_name} was purchased using {flow_event.sell_asset}. Multiple purchase currencies not supported yet.")

    def __str__(self):
        return f"{self.volume :< 20} {self.asset_name :<10} | Avg Price {self.buy_price} {self.buy_currency}"


class FlowEvent:
    def __init__(self, date, buy_asset, sell_asset, buy_volume, sell_volume):
        self.date = date
        self.buy_asset = buy_asset
        self.sell_asset = sell_asset
        self.buy_volume = float(buy_volume)
        self.sell_volume = float(sell_volume)
        self.unit_price = self.sell_volume/self.buy_volume

    def __str__(self):
        return f"{self.date} BUY {self.buy_volume} of {self.buy_asset}, SELL {self.sell_volume} of {self.sell_asset}. Unit price: {self.unit_price}"
