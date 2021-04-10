from pprint import pprint

import util
from cfg import tdcols


def process_trade_history(filepath):
    res = {}
    rows = util.load_csv(filepath)

    pairs = util.get_all_instances(rows, tdcols["pair"])
    # pprint(rows)

    avg_price = {}
    for pair in pairs:
        pair_rows = util.filter_by_kv(rows, tdcols["pair"], pair)
        sell_pair_rows = util.filter_by_kv(pair_rows, tdcols["side"], "SELL")
        buy_pair_rows = util.filter_by_kv(pair_rows, tdcols["side"], "BUY")
        if len(sell_pair_rows) > 0:
            avg_price[f"{pair}_SELL"] = util.weighted_average(
                sell_pair_rows, tdcols["executed"], tdcols["price"])
        if len(buy_pair_rows) > 0:
            avg_price[f"{pair}_BUY"] = util.weighted_average(
                buy_pair_rows, tdcols["executed"], tdcols["price"])

    # pprint(avg_price)
    res["Mean Buy Price"] = avg_price
    return res
