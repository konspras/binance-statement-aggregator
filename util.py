from cfg import names


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


def sum_by_coin(rows):
    '''
    rows: list of dicts
    Returns the sum of changes for each coin (coin->sum)
    '''
    sums = {coin: 0.0 for coin in get_all_instances(rows, names["coin"])}
    for row in rows:
        sums[row[names["coin"]]] += float(row[names["change"]])
    return sums
