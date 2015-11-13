from collections import Counter
from matplotlib import pyplot as plt
import csv


DICTIONARY_FILENAME = 'data/CollegeScorecardDataDictionary-09-12-2015.csv'
DATA_FILENAME = 'data/MERGED2011_PP.csv'
NAME_KEY_INDEX = 3


def is_null(row, key, count_private_as_null=True):
    return row[key] == 'NULL' or (count_private_as_null and row[key] == 'PrivacySuppressed')

def explore_nulls(keys, rows):
    debt_key = keys.index('GRAD_DEBT_MDN')
    earnings_key = keys.index('md_earn_wne_p6')
    degrees_key = keys.index('CIP01ASSOC')
    pcip_key = keys.index('PCIP01')
    rows = [row for row in rows if (
                not is_null(row, debt_key)
                and not is_null(row, earnings_key)
                and not is_null(row, degrees_key)
                and not is_null(row, pcip_key)
            )]

    num_null = {key: 0 for key in keys}
    both_debt_and_earnings_count = 0
    max_key_index = keys.index('RPY_1YR_RT')
    for row in rows:
        if not (row[debt_key] == 'NULL' or row[debt_key] == 'PrivacySuppressed') and not (
            row[earnings_key] == 'NULL' or row[earnings_key] == 'PrivacySuppressed'):
            both_debt_and_earnings_count += 1
        for i in xrange(max_key_index): #xrange(len(keys)):
            if is_null(row, i):
                num_null[keys[i]] += 1
    keys_by_nullity = sorted(keys, key=lambda k: num_null[k])
    print '%s of %s schools have the debt and earnings fields' % (both_debt_and_earnings_count, len(rows))

    preddeg_key = keys.index('PREDDEG')
    preddegs = [row[preddeg_key] for row in rows]
    print Counter(preddegs)
    sat_scores = []
    adm_rates = []
    sat_key = keys.index('SAT_AVG')
    adm_key = keys.index('ADM_RATE')
    for row in rows:
        if not is_null(row, sat_key):
            sat_scores.append(row[preddeg_key])
        if not is_null(row, adm_key):
            adm_rates.append(row[preddeg_key])
    print Counter(sat_scores)
    print Counter(adm_rates)

    reverse_counts = {}
    nulls_arr = []
    for key in keys:
        null_count = num_null[key]
        nulls_arr.append(null_count)
        # if 'earn' in key or 'RPY' in key or 'DEBT' in key:
        #     print '%5s %s' % (null_count, key)
        if null_count not in reverse_counts:
            reverse_counts[null_count] = 0
        reverse_counts[null_count] += 1
    
    '''
    keys_2159 = [keys.index(key) for key in keys if '_earn_wne_p8' in key]
    for row in rows:
        if all([row[k] == 'NULL' or row[k] == 'PrivacySuppressed' for k in keys_2159]):
            print '%s --- %s' % (row[NAME_KEY_INDEX], row[keys.index('PREDDEG')])
    '''

    plt.title('Keys that are non-NULL for at least one school')
    plt.xlabel('Number of schools for which key is NULL')
    plt.ylabel('Number of keys')
    plt.hist(nulls_arr)
    plt.show()

    with open('key_null_counts.txt', 'w') as outfile:
        outfile.write('Total schools: %s\n' % (len(rows)))
        outfile.write('Total number of keys: %s\n' % (len(keys)))
        outfile.write('Reverse counts: number of null to number of fields with that number null:\n')
        for null_count in sorted(reverse_counts):
            outfile.write('%5s %s\n' % (reverse_counts[null_count], null_count))
        outfile.write('Null counts by key:\n')
        for key in keys_by_nullity:
            outfile.write('%5s %s\n' % (num_null[key], key))
        outfile.write('School names')
        for row in rows:
            outfile.write('%s\n' % (row[NAME_KEY_INDEX]))


if __name__ == '__main__':
    with open(DATA_FILENAME, 'r') as data_file:
        raw_rows = [row for row in csv.reader(data_file)]
        keys, rows = raw_rows[0], raw_rows[1:]
        # explore_nulls(keys, rows)