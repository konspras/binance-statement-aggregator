import csv
import re
from datetime import datetime
from dateutil import parser

from cfg import trcols


def get_all_instances(rows, key):
    '''
    rows: list of dicts
    key: key of each dict, the values of which will be aggregated
    Returns a list of all the unique key value instances.
    '''
    instances = set()
    for row in rows:
        instances.update([row[key]])
    return list(instances)


def group_by_month(rows, datecol):
    '''
    Expects a list of dicts. The dicts must include a date column (datecol)
    Returns a dict of list of dicts keyed by month (month/year -> [entry])
    '''
    res = dict()
    for row in rows:
        key = get_month_year(row[datecol])
        if key in res:
            res[key].append(row)
        else:
            res[key] = [row]
    return res


def sum_by_coin(rows):
    '''
    rows: list of dicts
    Returns the sum of changes for each coin (coin->sum)
    '''
    sums = {coin: 0.0 for coin in get_all_instances(rows, trcols["coin"])}
    for row in rows:
        sums[row[trcols["coin"]]] += float(row[trcols["change"]])
    return sums


def weighted_average(rows, weight_key, target_key):
    tsum = 0
    wsum = 0
    for row in rows:
        weight = float(remove_non_float_chars(row[weight_key]))
        tsum += float(row[target_key]) * weight
        wsum += weight
    return tsum/wsum


def get_month_year(date):
    '''
    Expects a date in string format  or datetime and returns
    <month>/<year> as xx/yyyy
    '''
    if not isinstance(date, datetime):
        date = parser.parse(date)
    return f"{date.month}/{date.year}"


def sort_flow_events(flow_events):
    flow_events.sort(key=lambda event: event.date)


def split_coin_pair(pair, possible_coins):
    first, second = "", ""
    found = False
    for pcoin in possible_coins:
        if pcoin in pair:
            found = True
            f, s = pair.split(pcoin)
            if f:
                first = f
                second = pcoin
            else:
                first = pcoin
                second = s
            break

    # Sanity check
    if (first not in possible_coins) or (second not in possible_coins):
        raise Exception(
            f"'{first}' or '{second}' not in list {possible_coins}")

    if found:
        return first, second
    else:
        raise Exception(
            f"Could not split pair {pair} using coins {possible_coins}")


def remove_non_float_chars(str):
    return re.sub("[^0-9^\.]", "", str)


def remove_float_chars(str):
    return re.sub("[0-9\.]", "", str)


def filter_by_kv(rows, key, value):
    '''
    rows: list of dicts.
    Returns the items of the list that have <value> in <key>
    '''
    return [row for row in rows if row[key] == value]


def load_csv(filename):
    '''
    Returns all lines of a csv (with header) as a list of dicts
    '''
    rows = []
    with open(filename) as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            rows.append(row)
    return rows
