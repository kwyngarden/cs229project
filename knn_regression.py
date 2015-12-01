'''TODO: docstring'''

import csv
import numpy as np


FEATURES_FILENAME = 'out_features.csv'
LABELS_FILENAME = 'out_labels.csv'
DATA_SPLIT_FILENAME = 'data_split_indices.csv'


def read_features_and_labels(features_filename=FEATURES_FILENAME, labels_filename=LABELS_FILENAME):
    with open(features_filename, 'r') as features_file:
        raw_rows = [row for row in csv.reader(features_file)]
        feature_names = raw_rows[0]
        feature_rows = [[float(val) for val in row] for row in raw_rows[1:]]
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


def get_knn_predictions(train, dev, k=10, weighting='uniform'):
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


def compute_percent_errors(all_labels, all_predictions):
    num_labels = len(all_labels[0])
    all_errors = [[] for _ in xrange(num_labels)]
    for labels, predictions in zip(all_labels, all_predictions):
        for i in xrange(num_labels):
            error = (predictions[i] - labels[i]) / labels[i]
            all_errors[i].append(abs(error))
    return [100.0 * np.mean(errors) for errors in all_errors]

    
if __name__=='__main__':
    print 'Reading features and labels...'
    feature_names, feature_rows, label_names, label_rows = read_features_and_labels()
    print '\nSplitting data...'
    train, dev, test = get_data_splits(feature_rows, label_rows)
    print '\nMaking KNN predictions...'
    predictions = get_knn_predictions(train, dev, k=7, weighting='inverse_distance')
    print '\nComputing errors...'
    percent_errors = compute_percent_errors([labels for features, labels in dev], predictions)
    for i in xrange(len(label_names)):
        print '%s: %s%% average error' % (label_names[i], percent_errors[i])
    print '\nDone.'