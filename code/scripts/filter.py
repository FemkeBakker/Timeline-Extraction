from nltk.corpus import stopwords
import pandas as pd
import pdfplumber
import spacy #typer==0.3.2
import re
import os
import aspose.words as aw
import glob
import csv
import numpy as np

from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import PDFPageAggregator
from pdfminer3.converter import TextConverter
import io


""" Open pdf file and return if file is text or imaged based """

def open_pdf(path, file_name, threshold=0.1):
    # SOURCE: Big part of the code is from Julian Venhuizen github 
    # https://github.com/julianvenhuizen/wob-letter-extraction/blob/main/scripts/preparation.py

    total_page_area = 0.0
    total_text_area = 0.0

    try:
        doc = pdfplumber.open("{}/{}".format(path, file_name))
        pages = doc.pages

        # calculate total text erea
        for page_number, page in enumerate(pages):
            total_page_area = total_page_area + abs(page.width * page.height)
            text_area = 0.0
            i = 0
            for i in range(len(page.chars)):
                text_area = text_area + abs(page.chars[i]['width'] * page.chars[i]['height'])
            total_text_area = total_text_area + text_area
            i += 1

        doc.close()

        percentage = total_text_area / total_page_area        

        # if pdf is text based, convert pdf into txt and add file to new folder
        if percentage >= threshold: 
            return("text", file_name)
        else:
            return(("image", file_name))

    except Exception as e:
        print(f"The following exception: {e}, occurred at {file_name}")
        return None
    

"""Function that gets all file names from folder"""
def extract_file_names(path):
      # extract all file names
      file_names = glob.glob("{}/*.pdf".format(path))

      # correct file names -> remove path
      file_names = [name.replace("{}\\".format(path), "") for name in file_names]
      return(file_names)


def pdf_to_txt(path, file, id_file, tag, new_path):
    # SOURCE: https://github.com/julianvenhuizen/wob-letter-extraction/blob/main/scripts/preparation.py

    doc = pdfplumber.open('{}/{}'.format(path, file))
    pages = doc.pages

    text=["File id: {}".format(id_file)," ", "File title: {}.".format(tag[1]), "\n"]

    # for every page in the document, add the text to the total text
    for i in enumerate(pages):
                    j = i[0]
                    page = pages[j]
                    text.append(page.extract_text())

    # save text in txt file
    file1=open(r"{}/{}.txt".format(new_path, id_file),"a", encoding="utf-8")
    file1.writelines(text)
    file1.close()
    return None


"""Function that convert text-based pdf into txt file"""
def filter_and_extract(path, new_path, threshold):

    # get all file names in dataset
    file_names = extract_file_names(path)
    counter_id = 0

    # create dataframe to save global information about the dataset
    df = pd.DataFrame(columns=['id', 'label', "file"])

    # create new folder, if does not exist
    if not os.path.exists(new_path):
        os.makedirs(new_path)

    for file in file_names:
        try:
            # check if pdf is text or image based
            tag = open_pdf(path, file, threshold)
            print(tag)

            if tag[0] == "text":

                # convert pdf into txt
                pdf_to_txt(path, file, counter_id, tag, new_path)

                # save information about id, text or image and filename
                df.loc[len(df.index)] = [counter_id, "text", file] 

                counter_id += 1

            else:
                # save information about id, text or image and filename
                df.loc[len(df.index)] = [counter_id, "image", file] 
                counter_id += 1

        except Exception as e:
            print(f"The following exception: {e}, occurred at {file, counter_id}")

    df.to_csv(f"{new_path}/info.csv")
    return (None)

# df = filter_and_extract("data/IMIpdfs", "data/yeet")

