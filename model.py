from cfg import base_coins, default_coin
import util


class PortfolioState:
    def __init__(self):
        self.date = None
        self.positions = {}  # asset to Position
        self.bootstrap_count = 0
        # self.positions = {}  # "sell-asset_buy-asset" to Position
        # self.base_positions = {}  # "sell-asset_buy-asset" to Position

    def profit(self, month):
        # TODO: only accounting for default_coin profits. Must convert to get the other profits
        # TODO: Euro profits are not in USD
        profit = 0
        for position in self.positions.values():
            if month in position.profit:
                profit += position.profit[month]
        return profit

    def fees(self, month):
        # fees = {'BNB': 0, 'BUSD': 0}  # TODO: fix
        fees = 0
        for position in self.positions.values():
            if month in position.fees:
                # for coin in fees:
                # if coin in position.fees[month]:
                fees += position.fees[month]
        return fees

    # def mean_price(self, coin):
    #     pos_key = self.__position_key_from_asset(coin)
    #     if pos_key in self.positions:
    #         return self.positions[pos_key].buy_price
    #     else:
    #         raise Exception(f"No position for {coin}")

    def add_event(self, event):
        if not isinstance(event, GenericEvent):
            raise Exception(f"Event {event} is not a GenericEvent")
        event = self.__convert_event(event)
        if self.date is None or event.date > self.date:
            self.date = event.date

        pos = self.__create_position(event)
        pos.update_position(event)

    # TODO: Must extend to work with all stablecoins such taht any conversion to
    # a stablecoin is profit taking.

    def __convert_event(self, event):
        if event.out_asset is None:
            # Distribution
            return DistributionEvent(event.date, event.in_asset, event.in_amount)
        else:
            fee_asset = event.fee_asset
            fee_amount = event.fee_amount
            if fee_asset and fee_asset != default_coin:
                self.__remove_from_balance(fee_asset, fee_amount)
                fee_amount = self.__convert_local(fee_asset, fee_amount)
            else:
                fee_amount = 0
            if event.in_asset == default_coin:
                # Profit taking
                # TODO: Should credit default coin back to position
                return SellEvent(event.date, event.in_amount, event.out_asset, event.out_amount, fee_amount)
            else:
                # Buy
                out_asset = event.out_asset
                out_amount = event.out_amount
                if out_asset != default_coin:
                    self.__remove_from_balance(out_asset, out_amount)
                    out_amount = self.__convert_local(out_asset, out_amount)
                return BuyEvent(event.date, event.in_asset, event.in_amount, out_amount, fee_amount)

    # This is kinda hacky
    def __remove_from_balance(self, currency, amount):
        if currency not in self.positions:
            print("!!! Currency not in positions !!!")
            return
        self.positions[currency].amount -= amount

    def __convert_local(self, currency, amount):
        # Converts to default_coin
        if currency not in self.positions:
            if self.bootstrap_count < 1:
                if currency == "BNB":
                    # Bootsraping issue
                    print(
                        f"!!!!!!!!!!!!!!!!!!!! Bootsraping issue no {self.bootstrap_count}!!!!!!!!!!!!!!!!!!!!")
                    print(self)
                    return 392.72 * amount
            # You don't have the asset
            raise Exception(f"Cannot convert {currency} to {default_coin}")
        return self.positions[currency].buy_price * amount

    def __create_position(self, event):
        pos = None
        if isinstance(event, SellEvent):
            if event.out_asset not in self.positions:
                self.positions[event.out_asset] = Position(
                    event.out_asset)
            pos = self.positions[event.out_asset]
        elif isinstance(event, BuyEvent) or isinstance(event, DistributionEvent):
            if event.in_asset not in self.positions:
                self.positions[event.in_asset] = Position(event.in_asset)
            pos = self.positions[event.in_asset]
        else:
            raise Exception(
                f"No create_position implementation for type {type(event)}")
        return pos

    def __str__(self):
        output = f"Portfolio state on {self.date}\n"
        output += f"Positions\n"
        for coin in self.positions:
            output += f"{str(self.positions[coin])}\n"
        return output


class Position:
    def __init__(self, asset_name):
        self.asset_name = asset_name
        self.amount = 0
        self.buy_price = 0  # In default_coin
        self.invested = 0  # In default_coin
        self.profit = {}  # month to profit/loss amount
        self.fees = {}  # month to coin to value

    def update_position(self, event):
        if isinstance(event, DistributionEvent):
            if event.in_asset in base_coins:
                self.__add_profit(event.date, event.in_amount)
            else:
                self.__update_price(0, event.in_amount)
            self.amount += event.in_amount
        elif isinstance(event, BuyEvent):
            buy_price = event.out_amount / event.in_amount
            self.__update_price(buy_price, event.in_amount)
            self.__add_fees(event.date, event.fee_amount)
            self.amount += event.in_amount
            self.invested += event.out_amount
        elif isinstance(event, SellEvent):
            sell_price = event.in_amount / event.out_amount
            # Exception until all events are included (including euro inflows)
            if event.out_asset not in base_coins:
                profit = (sell_price - self.buy_price) * event.out_amount
                self.__add_profit(event.date, profit)
            self.__add_fees(event.date, event.fee_amount)
            self.amount -= event.out_amount
            self.invested -= event.out_amount * self.buy_price
        else:
            raise Exception(
                f"Cannot update position. Unknown event class: {type(event)}")

    def __update_price(self, new_price, new_amount):
        self.buy_price = (self.buy_price * self.amount +
                          new_price * new_amount) / (self.amount + new_amount)

    def __add_profit(self, date, profit):
        month_year = util.get_month_year(date)
        if month_year not in self.profit:
            self.profit[month_year] = 0
        self.profit[month_year] += profit

    def __add_fees(self, date, fee_amount):
        month_year = util.get_month_year(date)
        if month_year not in self.fees:
            self.fees[month_year] = 0
        self.fees[month_year] += fee_amount

    def __str__(self):
        amount = round(self.amount, 4)
        buy_price = "-"
        # TODO: bad comparison
        if amount == 0:
            amount = "-"
        if self.buy_price is not None:
            buy_price = round(self.buy_price, 4)
        return f"{amount :<12} {self.asset_name :<8} | Avg Price {buy_price :<10} | Profit {self.profit} | Fees {self.fees}"


class GenericEvent:
    def __init__(self, date, in_asset, out_asset, fee_asset, in_amount, out_amount, fee_amount):
        self.date = date
        self.in_asset = in_asset
        self.out_asset = out_asset
        self.fee_asset = fee_asset
        self.in_amount = float(in_amount) if in_amount is not None else None
        self.out_amount = float(
            out_amount) if out_amount is not None else None
        self.fee_amount = float(fee_amount) if fee_amount is not None else None

    # TODO: do arg validation
    def __str__(self):
        return f"{self.date} IN {self.in_amount} {self.in_asset}, " +\
            f"OUT {self.out_amount} {self.out_asset}. " +\
            f"FEE {self.fee_amount} {self.fee_asset})"


class DistributionEvent:
    def __init__(self, date, in_asset, in_amount):
        self.date = date
        self.in_asset = in_asset
        self.in_amount = in_amount

    def __str__(self):
        return f"{self.date} IN {self.in_amount} {self.in_asset}"


class BuyEvent:
    """
    Everything is in reference to default_coin
    """

    def __init__(self, date, in_asset, in_amount, out_amount, fee_amount):
        self.date = date
        self.in_asset = in_asset
        self.in_amount = in_amount
        self.out_amount = out_amount
        self.fee_amount = fee_amount

    # TODO: cp paste
    def __str__(self):
        return f"{self.date} IN {self.in_amount} {self.in_asset}, " +\
            f"OUT {self.out_amount} {default_coin}. " +\
            f"(Fee {self.fee_amount} {default_coin})"


class SellEvent:
    """
    Everything is in reference to default_coin
    """

    def __init__(self, date, in_amount, out_asset, out_amount, fee_amount):
        self.date = date
        self.in_amount = in_amount
        self.out_asset = out_asset
        self.out_amount = out_amount
        self.fee_amount = fee_amount

    # TODO: cp paste
    def __str__(self):
        return f"{self.date} IN {self.in_amount} {default_coin}, " +\
            f"OUT {self.out_amount} {self.out_asset}. " +\
            f"(Fee {self.fee_amount} {default_coin})"
