from pprint import pprint

import util
from cfg import trcols, risk_free_coins


def calculate_fees(rows):
    fee_op = "Fee"
    fee_rows = [row for row in rows if row[trcols["operation"]] == fee_op]
    return util.sum_by_coin(fee_rows)


def process_transaction_history(filepath):
    res = {}
    rows = util.load_csv(filepath)
    accounts = util.get_all_instances(rows, trcols["account"])
    coins = util.get_all_instances(rows, trcols["coin"])
    ops = util.get_all_instances(rows, trcols["operation"])

    # rf_rows = [row for row in rows if row[trcols["coin"]] in risk_free_coins]

    # interest_op = "Savings Interest"
    # rf_interest_rows = [
    #     row for row in rows if row[trcols["operation"]] == interest_op]

    # sell_op = "Sell"
    # rf_sell_rows = [row for row in rows if row[trcols["operation"]] == sell_op]
    # # pprint(rf_sell_rows)

    fees = calculate_fees(rows)
    info = {"Accounts": accounts,
            "Coins": coins,
            "Operations": ops}
    res["Fees"] = fees
    res["info"] = info
    return res
