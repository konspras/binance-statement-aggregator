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
        date = parser.parse(row[datecol])
        key = f"{date.month}/{date.year}"
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


def remove_non_float_chars(str):
    return re.sub("[^0-9^\.]", "", str)


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
