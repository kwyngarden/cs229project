'''Featurization module.

This module is responsible for turning (filtered) data rows into featurized
examples (a tuple containing a list of features and a list of label values to
be predicted). Featurization steps include:

    - Splitting prediction fields (debt/earnings/repayment) from input fields
    - Discarding useless fields (example: number of students in data collection
        cohorts, given by fields ending with _N)
    - Adding features that indicate whether a field had a NULL value, replacing
        NULL with 0 in the original feature
    - Discarding non-numerical fields (or other handling)
    - Turning any categorical keys into indicator features (and a single NULL
        case)
'''

import csv
import read_data


DICTIONARY_FILENAME = 'data/CollegeScorecardDataDictionary-09-12-2015.csv'

LABEL_KEYS = [
    'GRAD_DEBT_MDN',
    'md_earn_wne_p6',
]


def is_prediction_key(key_row):
    # 'aid' fields that are not prediction keys
    if key_row[0] in ['pell_grant_rate', 'PCTFLOAN', 'loan_ever']:
        return True
    return key_row[2] in ['repayment', 'earnings', 'aid']


def is_category(key_row):
    return not key_row[0] and not key_row[1]


def get_categorical_keys(rows):
    categorical_keys = {}    
    current_category_key = None
    current_categories = []
    for row in rows:
        if current_category_key:
            if is_category(row):
                current_categories.append((row[7], row[8]))
            else:
                if len(current_categories) > 0:
                    categorical_keys[current_category_key] = current_categories
                current_category_key = row[4]
                current_categories = []
        elif not is_category(row):
            current_category_key = row[4]
            current_categories = []
        else:
            print 'ERROR: saw category before key'
    return categorical_keys


def get_examples(label_keys=LABEL_KEYS):
    rows, keys = read_data.get_filtered_rows()

    with open(DICTIONARY_FILENAME, 'r') as dict_file:
        key_rows = [row for row in csv.reader(dict_file)][1:]
    key_row_lookup = {key_row[4]: key_row for key_row in key_rows if key_row[4]}
    
    prediction_keys = set([
        key for key in keys
        if key in key_row_lookup and is_prediction_key(key_row_lookup[key])
    ])
    cohort_size_keys = set([
        key for key in keys
        if key.endswith('_N')
    ])
    label_indices = [keys.index(label_key) for label_key in label_keys]

    examples = []
    for row in rows:
        features = [1.0] # Include intercept term in features
        for i in xrange(len(keys)):
            if keys[i] not in prediction_keys and keys[i] not in cohort_size_keys:
                # TODO: specially handle categorical keys
                # TODO: add binary features for whether each key is NULL
                #       - TODO: How to deal with PrivacySuppressed?
                try:
                    value = float(row[i])
                    features.append(value)
                except ValueError:
                    features.append(0.0)
        labels = [row[label_index] for label_index in label_indices]
        examples.append((features, labels))
    return examples


if __name__=='__main__':
    examples = get_examples()
    print len(examples)
    print len(examples[0][0])
    # TODO: write these out to a file format that Matlab can easily read