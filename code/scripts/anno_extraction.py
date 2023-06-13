import json
import pandas as pd
from extraction import extract
from text_files_split import split_txt_files
from date_correction import uncorrected_dates
from train_test_split import split
import time


""" Prepare data after annotation """

# load json file with annotations into jsonobject
jsonObj = pd.read_json(path_or_buf="data/GT_doccano.jsonl", lines=True)

# extract data from json file -> save in 7 csv files with dataframes
extract(jsonObj, "data/GT/GT")

# split dataset into train and test set, using 50/50 split
split("data/GT/GT", "data/GT/GTtrain", "data/GT/GTtest")

# split txt files into seperate folders for test and training data
split_txt_files("data/preparation/txt_files/IMI_txt_0.1/", "data/preparation/txt_files/IMI_txt_train_0.1", "data/preparation/txt_files/IMI_txt_test_0.1")



# save uncorrected dates (part of algorithm) -> these dates are the first run, on the original date selection function
# these dates will later be corrected based on the training set. 
start = time.time()
uncorrected_dates("data/preparation/txt_files/IMI_txt_train_0.1/", "data/results/date_extraction", "train")
uncorrected_dates("data/preparation/txt_files/IMI_txt_test_0.1/", "data/results/date_extraction", "test")

print(f"Total runtime for trainingset:{round(time.time() - start)}")

