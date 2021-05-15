from pprint import pprint
from dateutil import parser
import util
from model import FlowEvent
from cfg import tdcols, coins_used


def extract_flow_events(rows, coins):
    res = []
    for row in rows:
        date = parser.parse(row[tdcols["date"]])
        coin1, coin2 = util.split_coin_pair(row[tdcols["pair"]], coins)

        coin1_amount = row[tdcols["amount"]]
        # coin1_amount = util.remove_non_float_chars(row[tdcols["executed"]])
        coin2_amount = row[tdcols["executed"]]
        # coin2_amount = util.remove_non_float_chars(row[tdcols["amount"]])
        op = row[tdcols["side"]]
        if op == "SELL":
            sell_asset = coin1
            buy_asset = coin2
            sell_amount = coin1_amount
            buy_amount = coin2_amount
        elif op == "BUY":
            sell_asset = coin2
            buy_asset = coin1
            sell_amount = coin2_amount
            buy_amount = coin1_amount
        else:
            raise Exception(f"Unknown operation type {op}")

        # fee_asset = util.remove_float_chars(row[tdcols["fee"]])
        fee_asset = row[tdcols["fee coin"]]
        if fee_asset not in coins:
            raise Exception(f"Fee coin {fee_asset} is not in {coins}")
        fee_amount = row[tdcols["fee"]]
        res.append(FlowEvent(date, buy_asset,
                             sell_asset, fee_asset, buy_amount, sell_amount, fee_amount))
    return res


def clean_data(rows):
    for row in rows:
        row[tdcols["price"]] = float(row[tdcols["price"]].replace(',', ''))


def process_trade_history(filepath):
    res = {}
    info = {}
    rows = util.load_csv(filepath)

    clean_data(rows)

    flow_events = extract_flow_events(rows, coins_used)
    pairs = util.get_all_instances(rows, tdcols["pair"])
    info["Pairs"] = pairs

    # rows_by_month = util.group_by_month(rows, tdcols["date"])
    # # TODO: Revamp
    # avg_price = {}
    # for month in rows_by_month:
    #     if month not in res:
    #         res[month] = {}
    #     for pair in pairs:
    #         pair_rows = util.filter_by_kv(rows, tdcols["pair"], pair)
    #         sell_pair_rows = util.filter_by_kv(
    #             pair_rows, tdcols["side"], "SELL")
    #         buy_pair_rows = util.filter_by_kv(pair_rows, tdcols["side"], "BUY")
    #         if len(sell_pair_rows) > 0:
    #             avg_price[f"{pair}_SELL"] = util.weighted_average(
    #                 sell_pair_rows, tdcols["executed"], tdcols["price"])
    #         if len(buy_pair_rows) > 0:
    #             avg_price[f"{pair}_BUY"] = util.weighted_average(
    #                 buy_pair_rows, tdcols["executed"], tdcols["price"])
    #         res[month]["Mean Buy Price"] = avg_price

    return flow_events, info
    # return flow_events, res, info
