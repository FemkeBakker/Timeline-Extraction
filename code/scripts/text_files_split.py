""" Split IMItext folder into training and test folder, with txt files"""

import os
import pandas as pd
import shutil

""" Get the ids from the training and test set """
def get_test_train_ids():
    df_train = pd.read_csv("data/GT/GTtrain/date_event_combinations.csv")
    df_test = pd.read_csv("data/GT/GTtest/date_event_combinations.csv")
    train_ids = set(list(df_train['doc_id'].values))
    test_ids = set(list(df_test['doc_id'].values))
    return train_ids, test_ids


""" Split folder into text and training folder """
def split_txt_files(source_folder, train, test):
    train_ids, test_ids = get_test_train_ids()

    # Create the destination folders if they don't exist
    os.makedirs(train, exist_ok=True)
    os.makedirs(test, exist_ok=True)


    c_train = 0
    c_test = 0
    for filename in os.listdir(source_folder):
        if filename.endswith(".txt"):
            id = int(filename.replace(".txt", ""))
            source_file = os.path.join(source_folder, filename)
            if id in train_ids:  # Replace "criteria" with your desired condition
                destination_file = os.path.join(train, filename)
                c_train += 1
                shutil.copy(source_file, destination_file)
            elif id in test_ids:

                destination_file = os.path.join(test, filename)
                c_test += 1
                shutil.copy(source_file, destination_file)


