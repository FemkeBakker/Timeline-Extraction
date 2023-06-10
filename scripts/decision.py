import pandas as pd
import re
from sklearn.metrics import *


"""Classify if date is decision date"""
def decision_class(df):
    df_copy = df.copy()
    classes = []
    for index, row in df.iterrows():
        # set default prediction
        prediction = False
        sent = row['sentence']

        # select words before date in sentence
        before_date = sent[:row['start_in_sent']]

        # decision date is usually indicated by Datum
        patterns = ['Datum', "D atum"]
        for pattern in patterns:
            if re.search(pattern, before_date):
                # if Datum in words before date, then predict true
                prediction = True
                break
        classes.append(prediction)

    # add predictions to dataframe
    df_copy['decisiondate'] = classes

    # sort values on doc and appearance in doc
    df_copy = df_copy.sort_values(['doc_id', "start_in_text"])


    ids = list(set(df_copy['doc_id'].values))
    for i in ids:
        # select all dates per document
        df_doc = df_copy.loc[df_copy['doc_id'] == i]

        # select all dates that were classified as decisiondate
        decisions = df_doc.loc[df_doc['decisiondate'] == True]
        indexes = decisions.index.values.tolist()

        # if more then one decisiondate is selected per doc, then select first date
        if len(decisions) > 1:
            indexes = indexes[1:]
            df_copy.loc[indexes,'decisiondate'] = False


        if len(decisions) == 0:
            for index, row in df_doc.iterrows():
                first_index = row.name
                break

            df_copy.loc[first_index, 'decisiondate'] = True
    return df_copy


"""Evaluate decision date prediction"""
def evaluate_decision(df, gt):
    df_copy = df.copy()
    truths = []
    for index, row in df.iterrows():
        # set default truth
        truth = False

        # select gt of date
        gt_row = gt.loc[(gt['text'] == row['date']) & (gt['sentence'] == row['sentence']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text'])]
        
        # check for bug
        if len(gt_row) > 1:
            print("error message: more then one match with ground truth")

        # if a row is selected, means that date is a date with an event
        elif len(gt_row) == 1:

            # check if date is classified as decision date in gt
            if gt_row['label'].values[0] == "c: besluit datum":
                truth = True
            else:
                truth = False
        truths.append(truth)

    # calculate evaluation metrics
    accuracy = accuracy_score(truths, list(df['decisiondate'].values))
    recall = recall_score(truths, list(df['decisiondate'].values))
    precision = precision_score(truths, list(df['decisiondate'].values))
    f1 = f1_score(truths, list(df['decisiondate'].values))


    tn, fp, fn, tp = confusion_matrix(truths, list(df['decisiondate'].values)).ravel()
    values = {"fp": fp, "tp":tp, "fn":fn, "tn":tn}

    # add truths too dataframe
    df_copy['truth'] = truths

    return accuracy, recall, precision, f1, values, df_copy
  