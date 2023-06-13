try:
    from sentences_py import select_sentences, edit_text, load_text
except ModuleNotFoundError:
    from code.scripts.sentences_py import select_sentences, edit_text, load_text

import spacy
import pandas as pd
import re
import os
import pickle

from collections import Counter

"""extract all dates, save the begin and end character of each date, adjusted for this"""
def extract_dates(sent, text, pre_sent):
    nlp = spacy.load("nl_core_news_sm")
    sent = sent.strip()
    doc = nlp(sent) 

    # if sentence is duplicate in text, make sure to get the right one
    if sent != pre_sent:
        start = text.find(sent)
        end = start + len(sent)

    else:
        start = text.rfind(sent)
        end = start + len(sent)


    # regex patterns will match false dates
    # TODO: meuk aantoevoegen
    rgx_matches = [".*\.+.*", "\d\d\d\d\d", ".*:.*", "2[1-9][0-9][0-9]", "[0-9][0-9][0-9][0-9]-[0-9][0-9]", "\D* (?:weken|jaar)", "^[0-9][0-9][0-9]$", "^[2-9][1-9][0-9][0-9]$", "^[3-9][0-9][0-9][0-9]$"]
    results = []
    for ent in doc.ents:
        # print(ent)
        if ent.label_ == 'DATE':

            # check all patterns
            matches = []
            for rgx in rgx_matches:
                match = re.findall(rgx, ent.text)

                if len(match) != 0:
                    matches.append(match)

            # test date further if date is not nonsense, test if date is complete. 
            if len(matches) == 0:
             
                start_date = start + ent.start_char
                end_date = start_date + len(ent.text)

                results.append((ent.text, ent.label_, start_date, end_date, ent.start_char, ent.end_char, doc.text))


    return results


""" Extract dates from decision letters using the original method, used as preparation of the dataset for annotation"""
def get_first_results(path):
    documents, ids = load_text(path)
    result_dict = dict()

    for i in range(len(ids)):
        doc = documents[i]
        id = ids[i]
        print(f"at document {i+1} out of {len(ids)}")

        # split text into sentences
        sent = edit_text(doc)

        # select sentencences with dates
        text, sentences = select_sentences(sent)

        # get all entities labelled "DATE" by spaCy
        results = []
        sentences = sorted(sentences)
        for i in range(len(sentences)):
            results.extend(extract_dates(sentences[i], text, sentences[i-1]))

        # do no select first sentence -> title & id
        result_dict[id] = results
         

    return result_dict

""" Function corrects single dates (does not combine period dates)"""
def correct_dates(result):
    date = result[0]
    label = result[1]
    start_text = result[2]
    end_text = result[3]
    start_sent = result[4]
    end_sent = result[5]
    sent = result[6]

    standard_pattern = "^[0-9][0-9]?\s(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s[0-2][0-9][0-9][0-9]$"
    corrected = False
    

    # date MIGHT not be complete
    if not re.match(standard_pattern, date):

        # word after date
        # after_date = sent[end:].strip()
        after_date = sent[end_sent:].strip()

        # check if jl after date
        match = re.search(r"^jl", after_date)
        if match:
            matched_string = match.group()
            date = f"{date} {matched_string}"
            end_sent += match.end() + 1
            end_text += match.end() + 1

            corrected = True
        
        # check if year after date:
        match = re.search(r"^[0-2][0-9][0-9][0-9]", after_date)
        if match:
            matched_string = match.group()
            date = f"{date} {matched_string}"
            end_sent += match.end() + 1
            end_text += match.end() + 1

            corrected = True


        # check if more months
        pattern = "^, (?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december) en (?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)"
        match = re.search(pattern, after_date)
        if match:
            matched_string = match.group()
            date = f"{date}{matched_string}"
            end_sent += match.end() 
            end_text += match.end() 

            corrected = True

        # word before date
        before_date = sent[:start_sent].strip()

        # check if day before date
        match = re.search(r" [0-9]?[0-9] en$", before_date)
        if match:
            matched_string = match.group().strip()
            date = f"{matched_string} {date}"
            start_sent -= match.end() - match.start() 
            start_text -= match.end() - match.start() 
            corrected = True

    if re.match(standard_pattern, date):
        # word before date
        before_date = sent[:start_sent].strip()

        # check if day before date
        match = re.search(r" [0-9]?[0-9] en$", before_date)
        if match:
            matched_string = match.group().strip()
            date = f"{matched_string} {date}"
            start_sent -= match.end() - match.start() 
            start_text -= match.end() - match.start() 
            corrected = True

        match = re.search(r"periode vanaf$", before_date)
        if match:
            matched_string = match.group()
            date = f"{matched_string} {date}"
            start_sent -= match.end() - match.start() +1
            start_text -= match.end() - match.start() +1

            corrected = True



    return ((date, label, start_text, end_text, sent, start_sent, end_sent, corrected))

""" Correct all dates in necessary, save all dates in csv file"""
def get_second_results(first_results):
    second_results = pd.DataFrame(columns=["doc_id", "date", "label", "corrected", "start_in_text", "end_in_text", "start_in_sent","end_in_sent", "sentence"])
    for i in first_results:
        for k in first_results[i]:
            doc = correct_dates(k)
            second_results.loc[len(second_results.index)] = [i, doc[0], doc[1], doc[7], doc[2], doc[3], doc[5], doc[6],doc[4]] 
    return second_results

def correct_dubble_dates(df_results):

    ids = set(df_results['doc_id'].values)
    matches = ["^en op$", "^en$", "^respectievelijk$"]
    cor_dates = pd.DataFrame(columns=["doc_id", "date", "label", "corrected", "start_in_text", "end_in_text", "start_in_sent","end_in_sent", "parts","sentence"])
    new_results = df_results.copy()
    remove_list = []
    
    for doc_id in ids:
        # select dataframe with only currect id
        df = df_results.loc[df_results['doc_id'] == doc_id]

        # select only sentences with more then one date
        sent_c = Counter(df['sentence'].values)
        sentences = [sent for sent in sent_c if sent_c[sent] > 1]


        # check for each sentence if dates need to be merged
        for sent in sentences:
            df_sent = df.loc[df['sentence'] == sent]

            for i in range(len(df_sent)-1):
                # select current row, next row and the text in between the dates
                cur_row = df_sent.iloc[i]
                next_row = df_sent.iloc[i+1]

                text_in_between = sent[cur_row['end_in_sent']:next_row['start_in_sent']].strip()

                # filter out only year dates
                year_match = "^\d\d\d\d$"
                cur_match = re.search(year_match, cur_row['date'])
                next_match = re.search(year_match, next_row['date'])
                if not cur_match and not next_match:

                    # check if in between text matches, if so append row
                    for m in matches:
                        match = re.search(m, text_in_between) 
                        if match:
                            date = sent[cur_row['start_in_sent']:next_row["end_in_sent"]]
                            cor_dates.loc[len(cor_dates.index)] = [cur_row['doc_id'], date, "DATE", [cur_row['corrected'], next_row['corrected']], 
                                                                cur_row['start_in_text'], next_row['end_in_text'], cur_row["start_in_sent"], 
                                                                next_row['end_in_sent'], [cur_row['date'], next_row['date']], sent] 
                            

                        
                            new_results.loc[len(new_results.index)] = [cur_row['doc_id'], date, "DATE", "combined", 
                                                                cur_row['start_in_text'], next_row['end_in_text'], cur_row["start_in_sent"], 
                                                                next_row['end_in_sent'], sent, ]
                            
                            remove_list.append(cur_row.name)
                            remove_list.append(next_row.name)
                            

                            break
    
    new_results = new_results.drop(remove_list)

    return new_results

def uncorrected_dates(path, new_path, label):
    first_results = get_first_results(path)

    if not os.path.exists(new_path):
        os.makedirs(new_path)

    with open(f'{new_path}/uncorrected_dates_{label}.pkl', 'wb') as fp:
        pickle.dump(first_results, fp)

def remove_non_dates(df):
    df_copy = df.copy()

    for index, row in df.iterrows():
        # match any date including a month. Lowercase date to include more dates. 
        match = re.search(r"(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)", row['date'].lower())
        if not match:
            df_copy = df_copy.drop([row.name])

    return df_copy


def accuracy_dates(gt, results):
    ids = list(set(gt['doc_id'].values))
    results_copy = results.copy()
 
    tot = len(gt)
    corr = 0
    not_found = 0

    for doc_id in ids:
        gt_doc = gt.loc[gt['doc_id'] == doc_id]
        res_doc = results.loc[results['doc_id'] == doc_id]

        for index, row1 in gt_doc.iterrows():
            found = False
            for index, row2 in res_doc.iterrows():
                if row1['text'] == row2['date'] and row1['start'] == row2['start_in_text'] and row1['end'] == row2['end_in_text'] and row1['sentence'] == row2['sentence']:
                    corr+=1
                    found = True
                    break

            if found == False:
                not_found += 1

                for index, row2 in res_doc.iterrows():
                    if (row1['start'] == row2['start_in_text'] or row1['end'] == row2['end_in_text']) and row1['sentence'] == row2['sentence']:
                        results_copy = results_copy.drop(index)


    accuracy = corr/tot
    return accuracy, not_found, results_copy

def compile(df):
    results_train = get_second_results(df)
    train_corrected = correct_dubble_dates(results_train)
    train_corrected = remove_non_dates(train_corrected)
    return train_corrected

