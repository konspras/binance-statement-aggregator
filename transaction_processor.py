from pprint import pprint
import datetime
from dateutil import parser

import util
from cfg import trcols, base_coins
from model import FlowEvent


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


def extract_flow_events(rows, coins, known_ops):
    res = []
    for row in rows:
        date = parser.parse(row[trcols["date"]])
        coin = row[trcols["coin"]]
        op = row[trcols["operation"]]
        change = row[trcols["change"]]
        flow_event = None
        # TODO: ignoring transaction related. Eur to BUSD coversion totals will
        # not be the same in portfolio state as they are in the transaction proc results.

        # Not counting sell, buy and fee twice
        interest_ops = ["Launchpool Interest",
                        "Savings Interest", "POS savings interest", "Commission History"]
        if op in interest_ops:
            flow_event = FlowEvent(date, coin,
                                   None, None, change, 0, 0)
        else:
            if op not in known_ops:
                raise Exception(f"Operation {op} not in known ops. Adapt code")
        if flow_event:
            res.append(flow_event)

    return res


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

    known_ops = returned_ops.copy()
    known_ops.append("Savings purchase")
    known_ops.append("Transaction Related")
    known_ops.append("Savings Principal redemption")
    known_ops.append("POS savings purchase")
    flow_events = extract_flow_events(rows, coins, known_ops)
    return flow_events, result, info
