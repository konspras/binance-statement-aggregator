from pprint import pprint
import datetime

import util
from cfg import trcols, risk_free_coins


def calculate_sum_by_op(rows, op):
    op_rows = [row for row in rows if row[trcols["operation"]] == op]
    return util.sum_by_coin(op_rows)


def process_transaction_history(filepath):
    res = {}
    rows = util.load_csv(filepath)

    accounts = util.get_all_instances(rows, trcols["account"])
    coins = util.get_all_instances(rows, trcols["coin"])
    ops = util.get_all_instances(rows, trcols["operation"])
    info = {"Accounts": accounts,
            "Coins": coins,
            "Operations": ops}
    # rf_rows = [row for row in rows if row[trcols["coin"]] in risk_free_coins]

    # What is "Commission History"?
    # Where are beth distributions?
    ops = ["Deposit", "Withdraw", "Fee", "Savings Interest", "Launchpool Interest",
           "Buy", "Sell", "Transaction Related", "POS savings interest"]
    rows_by_month = util.group_by_month(rows, trcols["date"])
    for month in rows_by_month.keys():
        if month not in res:
            res[month] = {}
        for op in ops:
            res[month][op] = calculate_sum_by_op(rows_by_month[month], op)
    return res, info
