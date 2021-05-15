from cfg import base_coins, default_coin
import util


class PortfolioState:
    def __init__(self):
        self.date = None
        self.positions = {}  # "sell-asset_buy-asset" to Position
        self.base_positions = {}  # "sell-asset_buy-asset" to Position

    def profit(self, month):
        # TODO: only accounting for BUSD profits. Must convert to get the other profits
        profit_def = 0
        for position in self.positions.values():
            if month in position.profit:
                if position.buy_currency == default_coin:
                    profit_def += position.profit[month]
        # TODO: Ugly: should have separate classes for base and general positions
        for position in self.base_positions.values():
            if month in position.profit:
                if position.buy_currency == default_coin:
                    profit_def += position.profit[month]
        return profit_def

    def fees(self, month):
        fees = {'BNB': 0, 'BUSD': 0}  # TODO: fix
        for position in self.positions.values():
            if month in position.fees:
                for coin in fees:
                    if coin in position.fees[month]:
                        fees[coin] += position.fees[month][coin]
                # TODO: add option to get fees in BUSD only. Somehow convert based on purchase price of BNB..
        return fees

    def mean_price(self, coin):
        pos_key = self.__position_key_from_asset(coin)
        if pos_key in self.positions:
            return self.positions[pos_key].buy_price
        else:
            raise Exception(f"No position for {coin}")

    def add_event(self, flow_event):
        print(flow_event)
        if self.date is None or flow_event.date > self.date:
            self.date = flow_event.date
        if self.__is_base_distribution(flow_event):
            # Distribution of base coin -> immediate profit
            self.__create_base_position(flow_event)
            self.base_positions[self.__position_key(flow_event)].update_position(
                flow_event, "base_distribution")  # TODO: make attribute of Position class
        elif self.__is_distribution(flow_event):
            self.__create_position(flow_event, True)
            self.positions[self.__position_key(flow_event)].update_position(
                flow_event, "distribution")
        elif self.__is_profit_taking(flow_event):
            if self.__position_key(flow_event, False) not in self.positions:
                print(self)
                raise Exception(
                    f"Position {self.__position_key(flow_event, False)} does not exist. Cannot sell it.")
            self.positions[self.__position_key(flow_event, False)].update_position(
                flow_event, "sell")
        elif self.__is_buy(flow_event):
            self.__create_position(flow_event, False)
            self.positions[self.__position_key(flow_event)].update_position(
                flow_event, "buy")
        else:
            raise Exception(f"Unknown flow event type. {flow_event}")

    def __is_base_distribution(self, flow_event):
        return flow_event.buy_asset in base_coins and self.__is_distribution(flow_event)

    def __is_distribution(self, flow_event):
        return (flow_event.sell_asset is None) and (flow_event.sell_amount is None) and\
            (flow_event.fee_asset is None) and (flow_event.fee_amount is None)

    def __is_profit_taking(self, flow_event):
        '''
        If the currency sold is a non reference one (EUR, USD, BUSD etc)
        and the currency bought is,
        then profit or loss on the position must be calculated.
        '''
        return (flow_event.sell_asset not in base_coins) and (flow_event.buy_asset in base_coins) and\
            (not self.__is_base_distribution(flow_event))

    def __is_buy(self, flow_event):
        return (flow_event.sell_asset is not None) and (flow_event.sell_amount is not None)

    def __create_position(self, flow_event, is_distribution):
        pos_key = self.__position_key(flow_event)
        if pos_key not in self.positions:
            self.positions[pos_key] = Position(
                flow_event.buy_asset, flow_event.sell_asset)
            if is_distribution:
                # TODO: this is not good. What if after it is registered as a distribution, I buy or sell in something other than the default_coin?
                self.positions[pos_key].buy_currency = default_coin
                self.positions[pos_key].buy_price = 0

    def __create_base_position(self, flow_event):
        pos_key = self.__position_key(flow_event)
        if pos_key not in self.base_positions:
            self.base_positions[pos_key] = Position(
                flow_event.buy_asset, flow_event.buy_asset)
            self.base_positions[pos_key].buy_price = None
    # TODO: This is a mess

    def __position_key(self, flow_event, is_buy=True):
        sell_asset = default_coin if flow_event.sell_asset is None else flow_event.sell_asset
        res = f"{sell_asset}_{flow_event.buy_asset}"
        if not is_buy:
            res = f"{flow_event.buy_asset}_{sell_asset}"
        print(res)
        return res

    def __position_key_from_asset(self, asset):
        return f"{default_coin}_{asset}"

    def __str__(self):
        output = f"Portfolio state on {self.date}\n"
        output += f"Positions\n"
        for coin in self.positions:
            output += f"{str(self.positions[coin])}\n"
        output += f"\nBase Positions\n"
        for coin in self.base_positions:
            output += f"{str(self.base_positions[coin])}\n"
        return output


class Position:
    def __init__(self, asset_name, buy_currency):
        self.asset_name = asset_name
        self.buy_currency = buy_currency
        self.amount = 0
        self.buy_price = 0
        self.invested = 0
        self.profit = {}  # month to profit/loss amount
        self.fees = {}  # month to coin to value

    def update_position(self, flow_event, op_type):
        print(flow_event)
        if op_type == "base_distribution":
            # TODO add checks
            self.__check_valid_base_distribution(flow_event)
            self.__add_profit(flow_event.date, flow_event.buy_amount)
        if op_type == "distribution":
            # TODO add ditsr checks
            new_amount = flow_event.buy_amount
            self.buy_price = (self.buy_price * self.amount) / \
                (self.amount + new_amount)
            self.amount += new_amount
        if op_type == "buy":
            if op_type == "buy":  # ugly
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
            self.__add_fees(flow_event)
            self.invested += flow_event.sell_amount
        elif op_type == "sell":
            self.__check_valid_sell(flow_event)
            sell_price = 1.0/flow_event.unit_price
            sell_income = sell_price * flow_event.sell_amount
            buy_cost = self.buy_price * flow_event.sell_amount

            profit = sell_income - buy_cost
            self.__add_profit(flow_event.date, profit)
            self.amount -= flow_event.sell_amount
            self.__add_fees(flow_event)

    def __add_profit(self, date, profit):
        month_year = util.get_month_year(date)
        if month_year not in self.profit:
            self.profit[month_year] = 0
        self.profit[month_year] += profit

    def __add_fees(self, flow_event):
        month_year = util.get_month_year(flow_event.date)
        if month_year not in self.fees:
            self.fees[month_year] = {}
        if flow_event.fee_asset not in self.fees[month_year]:
            self.fees[month_year][flow_event.fee_asset] = 0
        self.fees[month_year][flow_event.fee_asset] += flow_event.fee_amount

    def __check_valid_base_distribution(self, flow_event):
        if flow_event.buy_asset not in base_coins:
            raise Exception(
                f"Flow event's {flow_event} buy coin does not qualify as a base distr")

    def __check_valid_buy(self, flow_event):
        if self.asset_name != flow_event.buy_asset:
            raise Exception(
                f"This position is {self.asset_name} not {flow_event.buy_asset}")
        if self.buy_currency != flow_event.sell_asset:
            raise Exception(
                f"{self.asset_name} was purchased using {flow_event.sell_asset}. Multiple purchase currencies are not supported yet.")

    def __check_valid_sell(self, flow_event):
        # TODO: add more checks
        if flow_event.sell_amount > self.amount:
            raise Exception(
                f"Tried to sell more than the owned amount (owned {self.amount}, sell {flow_event.sell_amount}")

    def __str__(self):
        amount = round(self.amount, 4)
        buy_currency = self.buy_currency
        buy_price = "-"
        if amount == 0:
            amount = "-"
        if buy_currency is None:
            buy_currency = "-"
        if self.buy_price is not None:
            buy_price = round(self.buy_price, 4)
        return f"{amount :<12} {self.asset_name :<8} | Avg Price {buy_price :<10} {buy_currency :<6} - Invested: {round(self.invested,1):<10} | Profit ({self.buy_currency}){self.profit} | Fees {self.fees}"


class FlowEvent:
    def __init__(self, date, buy_asset, sell_asset, fee_asset, buy_amount, sell_amount, fee_amount):
        self.date = date
        self.buy_asset = buy_asset
        self.sell_asset = sell_asset
        self.fee_asset = fee_asset
        self.buy_amount = float(buy_amount) if buy_amount is not None else None
        self.sell_amount = float(
            sell_amount) if sell_amount is not None else None
        self.fee_amount = float(fee_amount) if fee_amount is not None else None
        if (self.sell_amount is not None) and (self.buy_amount is not None):
            self.unit_price = self.sell_amount/self.buy_amount
        else:
            self.unit_price = None

    # TODO: do arg validation
    def __str__(self):
        return f"{self.date} BUY {self.buy_amount} of {self.buy_asset}, " +\
            f"SELL {self.sell_amount} of {self.sell_asset}. Unit price: {self.unit_price} " +\
            f"(Fee {self.fee_amount} {self.fee_asset})"
