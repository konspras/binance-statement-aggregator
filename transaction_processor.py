from pprint import pprint
import datetime
from dateutil import parser

import util
from cfg import trcols, base_coins, considered_transaction_ops, coins_used
from model import GenericEvent


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

            print(f"coin {coin} not in {op_to_coin[op]}")
            print("~~")
            print(coin, op)
            # exit()
            op_to_coin[op][coin] = value
    else:
        print(f"op {op} not in {op_to_coin}")

        # print(op_to_coin)
        op_to_coin[op] = dict()
        op_to_coin[op][coin] = value
        # exit()


def extract_flow_events(rows, coins, known_ops):
    res = []
    ignored_events = []
    for row in rows:
        date = parser.parse(row[trcols["date"]])
        coin = row[trcols["coin"]]
        op = row[trcols["operation"]]
        change = row[trcols["change"]]
        flow_event = None
        # TODO: ignoring transaction related. Eur to BUSD coversion totals will
        # not be the same in portfolio state as they are in the transaction proc results.
        # Not counting sell, buy and fee here, but through trading data
        interest_ops = ["Launchpool Interest", "Distribution",
                        "Savings Interest", "POS savings interest", "Commission History"]
        deposit_ops = ["Deposit", "Withdraw"]
        if op in deposit_ops:
            flow_event = GenericEvent(
                date, coin, None, None, change, None, None, is_deposit=True)
        elif op in interest_ops:
            flow_event = GenericEvent(date, coin,
                                      None, None, change, None, None)
        else:
            if op not in known_ops:
                raise Exception(
                    f"Operation \"{op}\" not in known ops. Update known ops")
            if op not in ignored_events:
                ignored_events.append(op)
        if flow_event:
            res.append(flow_event)
    print(
        f"Transaction processor ignored the following event types:\n{ignored_events}")
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

    # rows_by_month = util.group_by_month(rows, trcols["date"])
    # for month in rows_by_month.keys():
    #     if month not in res:
    #         res[month] = {}
    #     for op in ops:
    #         res[month][op] = calculate_sum_by_op(rows_by_month[month], op)

    # # Merge "Transaction Related" in buy and sell
    # # TODO: Fix changing dict size
    # # for month in res:
    # #     for op in res[month]:
    # #         if op == "Transaction Related":
    # #             coin_to_value = res[month][op]
    # #             for coin in coin_to_value:
    # #                 val = coin_to_value[coin]
    # #                 new_op = "Sell" if val < 0 else "Buy"
    # #                 print("---------")
    # #                 print(res[month])
    # #                 add_to_coin_value(res[month], new_op, coin, val)

    # # returned_ops = ["Deposit", "Withdraw", "Fee", "Savings Interest", "Launchpool Interest",
    # #                 "Buy", "Sell", "POS savings interest", "Commission History"]
    # returned_ops = ["Deposit", "Withdraw", "Fee", "Savings Interest", "Launchpool Interest",
    #                 "Buy", "POS savings interest", "Commission History"]
    # result = dict()
    # for month in res:
    #     result[month] = dict()
    #     for op in returned_ops:
    #         result[month][op] = res[month][op]

    # consider "BNB deducts fee"
    flow_events = extract_flow_events(
        rows, coins_used, considered_transaction_ops)
    print(
        f"Transaction processor: data rows: {len(rows)} - events extracted: {len(flow_events)}")
    return flow_events, info
    # return flow_events, result, info
