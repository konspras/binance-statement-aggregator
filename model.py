from cfg import base_coins
import util


class PortfolioState:
    def __init__(self):
        self.date = None
        self.positions = {}  # coin to Position

    def add_trade(self, flow_event):
        if self.date is None or flow_event.date > self.date:
            self.date = flow_event.date
        # coin = flow_event.buy_asset
        # buy_currency = flow_event.sell_asset
        if self.__is_profit_taking(flow_event):
            if flow_event.sell_asset not in self.positions:
                raise Exception(
                    f"Position for coin {flow_event.sell_asset} does not exist. Cannot sell it.")
            self.positions[flow_event.sell_asset].update_position(
                flow_event, False)
        else:
            if flow_event.buy_asset not in self.positions:
                self.positions[flow_event.buy_asset] = Position(
                    flow_event.buy_asset, flow_event.sell_asset)
            self.positions[flow_event.buy_asset].update_position(
                flow_event, True)

    def __is_profit_taking(self, flow_event):
        '''
        If the currency sold is a non reference one (EUR, USD, BUSD etc)
        and the currency bought is,
        then profit or loss on the position must be calculated.
        '''
        if (flow_event.sell_asset not in base_coins) and (flow_event.buy_asset in base_coins):
            return True
        return False

    def __str__(self):
        output = f"Portfolio state on {self.date}\n"
        for coin in self.positions:
            output += f"{str(self.positions[coin])}\n"
        return output


class Position:
    def __init__(self, asset_name, buy_currency):
        self.asset_name = asset_name
        self.buy_currency = buy_currency
        self.amount = 0
        self.buy_price = None
        self.profit = {}  # month to profit/loss amount
        self.fees = {}  # month to coin to value

    # TODO: Must be able to make a position smaller or close it.
    # Add fake sell lines and see what happens
    # Must also be able to process Interest distributions
    def update_position(self, flow_event, is_buy):
        print("Update position")
        print(flow_event)
        if is_buy:
            self.__check_valid_buy(flow_event)
            new_amount = flow_event.buy_amount
            new_price = flow_event.unit_price
            if self.amount == 0:
                self.buy_price = new_price
                self.amount = new_amount
            else:
                self.buy_price = (self.buy_price * self.amount +
                                  new_price * new_amount) / (self.amount + new_amount)
                self.amount += new_amount
        else:
            # self.__check_valid_sell(flow_event)
            print(self)
            sell_price = 1.0/flow_event.unit_price
            # price_dif = self.buy_price - sell_price
            # print(price_dif)
            sell_income = sell_price * flow_event.sell_amount
            buy_cost = self.buy_price * flow_event.sell_amount

            profit = sell_income - buy_cost

            month_year = util.get_month_year(flow_event.date)
            if month_year not in self.profit:
                self.profit[month_year] = 0
            self.profit[month_year] += profit
            self.amount -= flow_event.sell_amount

    def __check_valid_buy(self, flow_event):
        if self.asset_name != flow_event.buy_asset:
            raise Exception(
                f"This position is {self.asset_name} not {flow_event.buy_asset}")
        if self.buy_currency != flow_event.sell_asset:
            raise Exception(
                f"{self.asset_name} was purchased using {flow_event.sell_asset}. Multiple purchase currencies are not supported yet.")

    # def __check_valid_sell(self, flow_event):
        # Amount sold must not be higher than amount bought

    def __str__(self):
        return f"{self.amount :< 20} {self.asset_name :<10} | Avg Price {self.buy_price} {self.buy_currency} | Profit {self.profit}"


class FlowEvent:
    def __init__(self, date, buy_asset, sell_asset, fee_asset, buy_amount, sell_amount, fee_amount):
        self.date = date
        self.buy_asset = buy_asset
        self.sell_asset = sell_asset
        self.fee_asset = fee_asset
        self.buy_amount = float(buy_amount)
        self.sell_amount = float(sell_amount)
        self.fee_amount = float(fee_amount)
        self.unit_price = self.sell_amount/self.buy_amount

    def __str__(self):
        return f"{self.date} BUY {self.buy_amount} of {self.buy_asset}, " +\
            f"SELL {self.sell_amount} of {self.sell_asset}. Unit price: {self.unit_price} " +\
            f"(Fee {self.fee_amount} {self.fee_asset})"
