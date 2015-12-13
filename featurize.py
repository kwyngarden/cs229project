'''Featurization module.

This module is responsible for turning (filtered) data rows into featurized
examples (a tuple containing a list of features and a list of label values to
be predicted). Featurization steps include:

    - Splitting prediction fields (debt/earnings/repayment) from input fields
    - Discarding useless fields (examples: number of students in data collection
        cohorts, given by fields ending with _N; any feature always NULL)
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


def is_null(row, key_index, count_private_as_null=False):
    return row[key_index] == 'NULL' or (count_private_as_null and row[key_index] == 'PrivacySuppressed')


def is_prediction_key(key_row):
    # 'aid' fields that are not prediction keys
    if key_row[0] in ['pell_grant_rate', 'PCTFLOAN', 'loan_ever']:
        return True
    return key_row[2] in ['repayment', 'earnings', 'aid']


def is_category(key_row):
    return not key_row[0] and not key_row[1]


def get_categorical_keys(key_rows):
    categorical_keys = {}    
    current_category_key = None
    current_categories = []
    for row in key_rows:
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


def get_non_feature_keys(rows, keys, key_row_lookup):
    prediction_keys = set([
        key for key in keys
        if key in key_row_lookup and is_prediction_key(key_row_lookup[key])
    ])
    cohort_size_keys = set([
        key for key in keys
        if key.endswith('_N')
    ])
    all_null_keys = set([
        keys[i] for i in xrange(len(keys))
        if all([is_null(row, i) for row in rows])
    ])
    non_numerical_keys = set(['INSTNM', 'STABBR', 'ZIP', 'CITY'])
    
    non_feature_keys = prediction_keys.union(
        cohort_size_keys).union(
        all_null_keys).union(
        non_numerical_keys)
    return non_feature_keys


def get_examples(label_keys=LABEL_KEYS):
    rows, keys = read_data.get_filtered_rows()

    with open(DICTIONARY_FILENAME, 'r') as dict_file:
        key_rows = [row for row in csv.reader(dict_file)][1:]
    key_row_lookup = {key_row[4]: key_row for key_row in key_rows if key_row[4]}
    
    non_feature_keys = get_non_feature_keys(rows, keys, key_row_lookup)
    privacy_suppressed_keys = set([
        keys[i] for i in xrange(len(keys))
        if any([row[i] == 'PrivacySuppressed' for row in rows])
    ])
    categorical_keys = get_categorical_keys(key_rows)

    label_indices = [keys.index(label_key) for label_key in label_keys]

    examples = []
    privacy_suppressed_values = []

    for row in rows:
        features = {}
        privacy_suppressed_features = {}
        for i in xrange(len(keys)):
            if keys[i] not in non_feature_keys:
                if keys[i] in privacy_suppressed_keys:
                    if is_null(row, i):
                        value = 0.0
                    elif row[i] == 'PrivacySuppressed':
                        value = -1.0
                    else:
                        value = float(row[i])
                    privacy_suppressed_features[keys[i]] = value
                else:
                    is_null_key = '%s_is_NULL' % (keys[i])
                    
                    if keys[i] in categorical_keys:
                        category_value_is_null = is_null(row, i)
                        features[is_null_key] = 1.0 if category_value_is_null else 0.0
                        for category_value, category_label in categorical_keys[keys[i]]:
                            category_key = '%s = %s' % (keys[i], category_label)
                            features[category_key] = (
                                1.0 if not category_value_is_null and row[i] == category_value
                                else 0.0
                            )
                    
                    else: # Non-categorical keys
                        # TODO: alternative ways of dealing with PrivacySuppressed?
                        if is_null(row, i):
                            features[keys[i]] = 0.0
                            features[is_null_key] = 1.0
                        else:
                            features[keys[i]] = float(row[i])
                            features[is_null_key] = 0.0
        
        # Arrange features alphabetically for more consistent ordering
        # between runs and easier exploration of the fitted model
        feature_values = [features[key] for key in sorted(features)]
        try:
            labels = [float(row[label_index]) for label_index in label_indices]
        except ValueError:
            labels = [row[label_index].strip() for label_index in label_indices]
        examples.append((feature_values, labels))
        privacy_suppressed_values.append([privacy_suppressed_features[key] for key in sorted(privacy_suppressed_features)])

    return examples, sorted(features), label_keys, privacy_suppressed_values, sorted(privacy_suppressed_features)


def find_all_0_features(examples, feature_names):
    nonzero_keys = set([])
    for features, labels in examples:
        for i in xrange(len(feature_names)):
            if features[i] > 0:
                nonzero_keys.add(feature_names[i])
    print 'Features with some nonzero values: %s' % len(nonzero_keys)
    return [name for name in feature_names if name not in nonzero_keys]

def get_features_with_single_value(examples, feature_names):
    all_value_sets = {i: set([]) for i in xrange(len(feature_names))}
    for features, labels in examples:
        for i in xrange(len(feature_names)):
            all_value_sets[i].add(features[i])
    return set([i for i in all_value_sets if len(all_value_sets[i]) <= 1])

def filter_features_with_single_values(examples, feature_names):
    features_with_single_value = get_features_with_single_value(examples, feature_names)
    new_examples = []
    for features, labels in examples:
        new_features = [
            features[i] for i in xrange(len(feature_names))
            if i not in features_with_single_value
        ]
        new_examples.append((new_features, labels))
    new_feature_names = [
        feature_names[i] for i in xrange(len(feature_names))
        if i not in features_with_single_value
    ]
    return new_examples, new_feature_names

def filter_privacy_suppressed_features(features, feature_names, required_percent=0.0):#7):
    filtered_features = [[] for _ in features]
    filtered_names = []
    
    for i, name in enumerate(feature_names):
        num_available = 0.0
        for row in features:
            if row[i] != -1.0:
                num_available += 1
        if num_available / len(features) >= required_percent:
            for row_index, row in enumerate(features):
                filtered_features[row_index].append(row[i])
            filtered_names.append(name)

    return filtered_features, filtered_names


if __name__=='__main__':
    examples, feature_names, label_names, privacy_suppressed_values, privacy_suppressed_names = get_examples()
    # examples, feature_names = filter_features_with_single_values(examples, feature_names)
    privacy_suppressed_values, privacy_suppressed_names = filter_privacy_suppressed_features(privacy_suppressed_values, privacy_suppressed_names)

    with open('new_out_features.csv', 'w') as features_file:
        with open('new_out_labels.csv', 'w') as labels_file:
            with open('new_privacy_suppressed_features.csv', 'w') as privacy_suppressed_file:
                features_file.write('%s\n' % (','.join([feature.replace(',', ';') for feature in feature_names])))
                labels_file.write('%s\n' % (','.join([label.replace(',', ';') for label in label_names])))
                privacy_suppressed_file.write('%s\n' % (','.join([name.replace(',', ';') for name in privacy_suppressed_names])))
                for features, labels in examples:
                    features_file.write('%s\n' % (','.join([str(feature) for feature in features])))
                    labels_file.write('%s\n' % (','.join([str(label) for label in labels])))
                for privacy_suppressed_line in privacy_suppressed_values:
                    privacy_suppressed_file.write('%s\n' % (','.join([str(feature) for feature in privacy_suppressed_line])))