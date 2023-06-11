import re
from nltk import tokenize
import spacy
import pandas as pd
import json
import os


def load_text(path):
    # get all file names/ids
    files = os.listdir(path)
    files = [int(file.replace(".txt", "")) for file in files if file.endswith(".txt")]
    files.sort()

    documents = []

    # for each file add the text to documents
    for i in files:
        with open('{}{}.txt'.format(path, i), 'r', encoding='utf-8') as file:
            text = file.read()
            documents.append(text)
            
    return documents, files

""" Clean up the doc by removing newlines & pagina nummers, 
split the text in sentences and return a list of sentences and a clean text."""
def edit_text(text):
    # first line contains file-id and name
    first = [tokenize.sent_tokenize(text)[0]]

    # second line contains gibberish from the side, but also decision date, and sometimes the first sentence. 
    second = tokenize.sent_tokenize(text)[1]

    third = []

    if "Geachte" in second:
        # get the index of the word "geachte"
        index = second.index("Geachte")

        # split the string into two based on the index
        third = [second[index+len("Geachte"):]]
        second = second[:index+len("Geachte")]
        
    if len(third) != 0:
        third_sentences = tokenize.sent_tokenize(third[0].replace("\n", " "))

    # remove enters
    text = text.replace("\n", " ")

    # remove point after jl., too make sure the splitting of sentences is done correctly
    rgx_match = "jl. [a-z]"
    replacement = "jl"
    text = re.sub(rgx_match, lambda match: replacement + match.group(0)[3:], text)

    # split text into sentences
    sentences = tokenize.sent_tokenize(text)

    # regex pattern for "Pagina d van dd"
    rgx_match = "Pagina \d+ van \d+"
    sentences = [re.sub(rgx_match, '', sent) for sent in sentences]

    # first sentence 
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(second)
    second_sentences = [str(sent).replace("\n", " ") for sent in doc.sents]

    if len(third) != 0:
        clean_sentences = first + second_sentences + third_sentences + sentences[2:]

    else:
        clean_sentences = first + second_sentences + sentences[2:] 

    # do not split sentences on "d.d."
    
    i = 0
    while i < len(clean_sentences) - 1:
        if clean_sentences[i].endswith('d.d.'):
            new_string = clean_sentences[i] + " " + clean_sentences[i+1]
            clean_sentences[i:i+2] = [new_string]
        else:
            i += 1

    
    return clean_sentences


""" Make a list of sentences with dates, make a text from only those sentences"""
def select_sentences(sentences):
    nlp = spacy.load("nl_core_news_sm")

    date_sentences = [sentences[0]]
    date_text = "{}\n\n\n".format(sentences[0])
    
    # regex patterns
    rgx_matches = [".*\.+.*", "\d\d\d\d\d", ".*:.*", "2[1-9][0-9][0-9]", "[0-9][0-9][0-9][0-9]-[0-9][0-9]", "\D* (?:weken|jaar)", "^[0-9][0-9][0-9]$", "^[2-9][1-9][0-9][0-9]$", "^[3-9][0-9][0-9][0-9]$"]

    for sent in sentences[1:]:

        doc = nlp(sent)
        counter = len(date_sentences)
        for ent in doc.ents:

            # only keep going if sentence isn't already added
            if counter < len(date_sentences):
                break

            # only add sentences that have a date
            if ent.label_ == "DATE":

                matches = []
                for rgx in rgx_matches:
                    match = re.findall(rgx, ent.text)
                    if len(match) != 0:
                        matches.append(match)
                    

                # if no matches, than there is at least one date in the sentence
                if len(matches) == 0:

                    # add sentence with date to list of sentences and text
                    date_sentences.append(sent)
                    date_text += " {}\n\n\n".format(sent)
                    break
    return date_text, date_sentences

"""extract all dates, save the begin and end character of each date"""
def extract_dates(text):
    nlp = spacy.load("nl_core_news_sm")
    doc = nlp(text) 

    # regex patterns will match false dates
    rgx_matches = [".*\.+.*", "\d\d\d\d\d", ".*:.*", "2[1-9][0-9][0-9]", "[0-9][0-9][0-9][0-9]-[0-9][0-9]", "\D* (?:weken|jaar)", "^[0-9][0-9][0-9]$", "^[2-9][1-9][0-9][0-9]$", "^[3-9][0-9][0-9][0-9]$"]

    results = []
    for ent in doc.ents:
        if ent.label_ == 'DATE':

            # check all patterns
            matches = []
            for rgx in rgx_matches:
                match = re.findall(rgx, ent.text)
                if len(match) != 0:
                    matches.append(match)

            # save date if it does not match with any pattern
            if len(matches) == 0:
                results.append([(ent.text, ent.label_, ent.start_char, ent.end_char)])

    return results

"""create df of labels"""
def create_char_df(text):
    results = extract_dates(text)
    df = pd.DataFrame(columns=['date', 'begin', 'end'])
    for row in results:
        df.loc[len(df.index)] = [row[0][0], row[0][2], row[0][3]] 
    return df

"""return list of labels, with label, begin character and end character"""
def get_labels(df):
    labels = []
    for index, row in df.iterrows():
        labels.append([row['begin'], row['end'], "DATE+"])
    return labels

"""save the text with labels in a json file"""
def save_to_json(text, labels, doc_id, path):
    file = {"text": text, 'label': labels}

    if not os.path.exists('{}/'.format(path)):
        os.makedirs('{}'.format(path))

    with open("{}/{}.json".format(path, doc_id), "w") as outfile:
        json.dump(file, outfile)

"""assemble all functions for each document"""
def edit_docs(documents, path, ids):

    # loop through documents, select sentences with dates, and label the dates
    for i in range(len(documents)):
        doc = documents[i]
        id_doc = ids[i]
        
        sentences = edit_text(doc)

        date_text, date_sentences = select_sentences(sentences)        
        df = create_char_df(date_text)
        labels = get_labels(df)
        save_to_json(date_text, labels, id_doc, path)

        id_doc+=1


# load file with doccano files - without annotations
# documents, ids = load_text("data/single/")
# edit_docs(documents, "data/single_try", ids)