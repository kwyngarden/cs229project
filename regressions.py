'''Module to run regressions on data from Python.'''

import csv
import numpy as np
from sklearn import svm


FEATURES_FILENAME = 'out_features.csv'
LABELS_FILENAME = 'out_labels.csv'
DATA_SPLIT_FILENAME = 'data_split_indices.csv'


def read_features_and_labels(features_filename=FEATURES_FILENAME, labels_filename=LABELS_FILENAME, feature_selection=None, use_privacy_suppressed=False):
    if use_privacy_suppressed:
        feature_names = None
        with open('combinedFeatures.csv', 'r') as features_file:
            raw_rows = [row for row in csv.reader(features_file)]
            feature_rows = [[float(val) for val in row] for row in raw_rows]
    else:
        with open(features_filename, 'r') as features_file:
            raw_rows = [row for row in csv.reader(features_file)]
            feature_names = raw_rows[0]
            feature_rows = [[float(val) for val in row] for row in raw_rows[1:]]
            if feature_selection:
                with open(feature_selection, 'r') as f:
                    indices = [int(s.strip()) for s in f.read().strip().split(',')]
                feature_rows = [[v for i, v in enumerate(row) if indices[i]] for row in feature_rows]
    with open(labels_filename, 'r') as labels_file:
        raw_rows = [row for row in csv.reader(labels_file)]
        label_names = raw_rows[0]
        label_rows = [[float(val) for val in row] for row in raw_rows[1:]]
    return feature_names, feature_rows, label_names, label_rows


def normalize_features(feature_rows):
    for i in xrange(len(feature_rows[0])):
        values = [row[i] for row in feature_rows]
        mean = np.mean(values)
        std = np.std(values)
        for j in xrange(len(feature_rows)):
            feature_rows[j][i] = (feature_rows[j][i] - mean) / std


def get_data_splits(feature_rows, label_rows):
    with open(DATA_SPLIT_FILENAME, 'r') as f:
        indices = [int(row.strip()) - 1 for row in f]
    train_indices = set(indices[:3500])
    dev_indices = set(indices[3500:4500])
    train, dev, test = [], [], []
    for i in xrange(len(feature_rows)):
        example = (feature_rows[i], label_rows[i])
        if i in train_indices:
            train.append(example)
        elif i in dev_indices:
            dev.append(example)
        else:
            test.append(example)
    return train, dev, test


def get_knn_predictions(train, dev, k=5, weighting='uniform'):
    predictions = []
    train_indices = [i for i in xrange(len(train))]
    iters = 0
    print 'Using k=%s and %s weighting' % (k, weighting)

    for features, labels in dev:
        iters += 1
        if iters == 1 or iters % 100 == 0 :
            print '\tIteration %s of %s' % (iters, len(dev))

        features = np.array(features)
        distances = {}
        for i in train_indices:
            other_features = np.array(train[i][0])
            distances[i] = np.linalg.norm(features - other_features)
        neighbors = sorted(train_indices, key=distances.get)[:k]
        
        weights = {i: 1.0 / k for i in neighbors}
        if weighting == 'inverse_distance':
            sum_inv_distances = sum([1.0 / distances[i] for i in neighbors])
            weights = {i: (1.0 / distances[i]) / sum_inv_distances for i in neighbors}
        elif weighting != 'uniform':
            print 'Unknown weighting scheme %s; defaulting to uniform weights' % (weighting)

        predicted_labels = np.zeros(len(labels))
        for i in neighbors:
            predicted_labels += weights[i] * np.array(train[i][1])
        predictions.append(predicted_labels)

    return predictions


def get_svm_predictions(train, dev):
    train_features = [features for features, labels in train]
    dev_features = [features for features, labels in dev]
    all_predictions = []
    for i in xrange(len(train[0][1])):
        model = svm.SVR(C=0.00000005)
        labels = [labels[i] for features, labels in train]
        model.fit(train_features, labels)
        all_predictions.append(model.predict(dev_features))

    predictions = []
    for i in xrange(len(all_predictions[0])):
        predictions.append([label_predictions[i] for label_predictions in all_predictions])
    return predictions


def compute_percent_errors(all_labels, all_predictions, use_rmse=False):
    num_labels = len(all_labels[0])
    all_errors = [[] for _ in xrange(num_labels)]
    for labels, predictions in zip(all_labels, all_predictions):
        for i in xrange(num_labels):
            error = (predictions[i] - labels[i]) / labels[i]
            if use_rmse:
                error = (error * labels[i]) ** 2
            all_errors[i].append(abs(error))
    
    def get_percent_error(errors):
        if use_rmse:
            return np.sqrt(np.mean(errors))
        return 100.0 * np.mean(errors)

    def get_std_error(errors):
        return 100.0 * np.std(errors) / np.sqrt(len(errors))

    return [get_percent_error(errors) for errors in all_errors], [get_std_error(errors) for errors in all_errors]

    
if __name__=='__main__':
    print 'Reading features and labels...'
    # feature_names, feature_rows, label_names, label_rows = read_features_and_labels(feature_selection='critical_features_debt.csv')
    feature_names, feature_rows, label_names, label_rows = read_features_and_labels(use_privacy_suppressed=True)
    train, dev, test = get_data_splits(feature_rows, label_rows)
    dev = test # Use test set for evaluation

    print '\nMaking predictions...'
    predictions = get_knn_predictions(train, dev, k=6, weighting='inverse_distance')
    # predictions = get_knn_predictions(train, dev, k=13, weighting='uniform')
    # predictions = get_svm_predictions(train, dev)
    
    print '\nComputing errors...'
    percent_errors, error_ranges = compute_percent_errors([labels for features, labels in dev], predictions)
    for i in xrange(len(label_names)):
        print '%s: %s +/- %s%% average error' % (label_names[i], percent_errors[i], error_ranges[i])
    print '\nDone.'