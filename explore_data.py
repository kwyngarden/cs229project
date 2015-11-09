from matplotlib import pyplot as plt
import csv


DATA_FILENAME = 'data/MERGED2003_PP.csv'
NAME_KEY_INDEX = 3


def explore_nulls(keys, rows, count_private_as_null=True):
    num_null = {key: 0 for key in keys}
    for row in rows[1:]:
        for i in xrange(len(keys)):
            if row[i] == 'NULL' or (count_private_as_null and row[i] == 'PrivacySuppressed'):
                num_null[keys[i]] += 1
    keys_by_nullity = sorted(keys, key=lambda k: num_null[k])

    reverse_counts = {}
    nulls_arr = []
    for key in keys:
        null_count = num_null[key]
        nulls_arr.append(null_count)
        if 'earn' in key or 'RPY' in key or 'DEBT' in key:
            print '%5s %s' % (null_count, key)
        if null_count not in reverse_counts:
            reverse_counts[null_count] = 0
        reverse_counts[null_count] += 1
    
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


if __name__ == '__main__':
    with open(DATA_FILENAME, 'r') as data_file:
        raw_rows = [row for row in csv.reader(data_file)]
        keys, rows = raw_rows[0], raw_rows[1:]
        explore_nulls(keys, rows)