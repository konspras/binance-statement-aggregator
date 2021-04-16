from pprint import pprint
import datetime

import util
from cfg import trcols, risk_free_coins


def calculate_sum_by_op(rows, op):
    '''
    Returns dict: coin-> value
    '''
    op_rows = [row for row in rows if row[trcols["operation"]] == op]
    return util.sum_by_coin(op_rows)


def add_to_coin_value(op_to_coin, op, coin, value):
    if op in op_to_coin:
        if coin in op_to_coin[op]:
            op_to_coin[op][coin] += value
        else:
            op_to_coin[op][coin] = value
    else:
        op_to_coin[op] = dict()
        op_to_coin[op][coin] = value


def process_transaction_history(filepath):
    res = {}
    rows = util.load_csv(filepath)

    accounts = util.get_all_instances(rows, trcols["account"])
    coins = util.get_all_instances(rows, trcols["coin"])
    ops = util.get_all_instances(rows, trcols["operation"])
    info = {"Accounts": accounts,
            "Coins": coins,
            "Operations": ops}

    # Where are beth distributions?

    rows_by_month = util.group_by_month(rows, trcols["date"])
    for month in rows_by_month.keys():
        if month not in res:
            res[month] = {}
        for op in ops:
            res[month][op] = calculate_sum_by_op(rows_by_month[month], op)

    # Merge "Transaction Related" in buy and sell
    for month in res:
        for op in res[month]:
            if op == "Transaction Related":
                coin_to_value = res[month][op]
                for coin in coin_to_value:
                    val = coin_to_value[coin]
                    new_op = "Sell" if val < 0 else "Buy"
                    add_to_coin_value(res[month], new_op, coin, val)

    returned_ops = ["Deposit", "Withdraw", "Fee", "Savings Interest", "Launchpool Interest",
                    "Buy", "Sell", "POS savings interest", "Commission History"]
    result = dict()
    for month in res:
        result[month] = dict()
        for op in returned_ops:
            result[month][op] = res[month][op]
    return result, info
