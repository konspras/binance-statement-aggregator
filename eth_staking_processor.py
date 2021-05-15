from pprint import pprint
import datetime
from dateutil import parser

import util
from cfg import ethstcols, bethdstrcols, base_coins, coins_used
from model import FlowEvent


def extract_stake_flow_events(rows):
    res = []
    for row in rows:
        date = parser.parse(row[ethstcols["date"]])
        in_coin = row[ethstcols["in"]]
        out_coin = row[ethstcols["out"]]
        amount_converted = row[ethstcols["amount"]]
        if in_coin != "BETH" or out_coin != "ETH":
            raise Exception(
                f"Expected in: BETH, out: ETH - got in: {in_coin}, out {out_coin}")
        fe = FlowEvent(date, in_coin, out_coin, None,
                       amount_converted, amount_converted, None)
        res.append(fe)
    return res


def extract_distr_flow_events(rows):
    res = []
    for row in rows:
        date = parser.parse(row[bethdstrcols["date"]])
        in_coin = row[bethdstrcols["in"]]
        amount = row[bethdstrcols["amount"]]
        if in_coin != "BETH":
            raise Exception(
                f"Expected in: BETH - got in: {in_coin}")
        fe = FlowEvent(date, in_coin, None, None,
                       amount, None, None)
        res.append(fe)
    return res


def process_eth_staking(th_stake_path, beth_distr_path):

    stake_rows = util.load_csv(th_stake_path)
    distr_rows = util.load_csv(beth_distr_path)
    stake_fe = extract_stake_flow_events(stake_rows)
    distr_fe = extract_distr_flow_events(distr_rows)
    res = stake_fe + distr_fe
    return res
