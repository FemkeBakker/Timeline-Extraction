import spacy
from sklearn.metrics import *
import pandas as pd
import numpy as np
import re
import time
import math
from collections import Counter
import string
import nltk
from nltk.corpus import stopwords
import openai
import os
from itertools import chain

"""Gets response of chatGPT using API"""
def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0, # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]

"""Generate text with date to classify"""
def ask_sentences(dates, sentences):
     # dates = list of dates
    # sentences = list of sentences
    # order of these lists is important, indexes match
    
    text = ""

    for i in range(len(dates)):
        text += f"{i+1}. Date = {dates[i]}\n"
        text += f"  - sentence = '{sentences[i]}'\n"
                # text += f"SENTENCE = {sentences[i]}\n"
        # text += "\n"
    return text

def tokenize_strings(strings):
    nlp = spacy.load("en_core_web_sm")
    tokenized_list = []
    for string in strings:
        doc = nlp(string)
        tokens = [token.text for token in doc]
        tokenized_list.extend(tokens)
    return tokenized_list

def remove_stopwords(tokens):
    stop_words = set(stopwords.words('dutch'))
    # remove dutch stopwords
    
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
    # remove tokens that exist out of 1 character
    filtered_tokens = [token for token in filtered_tokens if len(token) > 1]
    return filtered_tokens

def get_keys_above_threshold(dictionary, threshold):
    return [key for key, value in dictionary.items() if value >= threshold]

def important_tokens(gt_original):
    gt = gt_original.loc[gt_original['class'] != 'besluit datum']
    classes = list(set(gt['class'].values))
    class_dict = dict()
    for i in classes:
        gt_class = gt.loc[gt['class'] == i]
        events = list(gt_class['event'].values)
        tokens = tokenize_strings(events)
        tokens = [token for token in tokens if token not in string.punctuation]
        tokens = remove_stopwords(tokens)    
        important = get_keys_above_threshold(Counter(tokens), math.ceil(len(gt_class)/6))
        class_dict[i] = important

    return class_dict

def get_prompt(df, class_dict):
    dates = list(df['date'].values)
    sentences = list(df['sentence'].values)
    text = ask_sentences(dates, sentences)
    prompt = f"""

    Instructies: 
    Je taak is om de gebeurtenissen die op een bepaalde datum hebben plaatsgevonden te classificeren op basis van de gegeven zinnen. 
    Je krijgt een reeks zinnen, elk gekoppeld aan een specifieke datum. 
    Verder krijg je de definities van de klassen en tokens die vaak rondom datums van die klassen voorkomen in de zin. 
    Het doel is om elke zin toe te wijzen aan een van de volgende zeven klassen:
    1. "verzoek datum" = Op deze datum is een Woo verzoek ingediend. Op deze datum is er verzocht om informatie doormiddel van een Woo-verzoek. Op deze datum is gevraagd om openbaarmkaing van informatie. 
    Tokens "verzoek datum" = {class_dict['verzoek datum']}
    2. "verzoek ontvangen" = Op deze datum is een Woo verzoek ontvangen. 
    Tokens "verzoek ontvangen" = {class_dict['verzoek ontvangen']}
    3. "ontvangst verzoek bevestigd" = Op deze datum is bevestigd dat het verzoek ontvangen is. 
    Tokens "ontvangst verzoek bevestigd" = {class_dict['ontvangst verzoek bevestigd']}
    4. "beslistermijn verdaagd" = Op deze datum is de beslistermijn verdaagd, verplaatst of verlengd.
    Tokens "beslistermijn verdaagd" = {class_dict['beslistermijn verdaagd']}
    5. "inwerking treden van Woo" = Op 1 mei 2020 is de Woo inwerking getreden. Op 1 mei 2020 is de Wob vervangen door de Woo.
    Tokens "inwerking treden van Woo" = {class_dict['inwerking treden van Woo']}
    6. "contact" = Op deze datum heeft er communicatie plaatsgevonden.
    Tokens "contact" = {class_dict['contact']}
    7. "overig" = Als een datum niet onder een van de andere klassen valt.

    Dit zijn de {len(df)} datums die geclassificeerd moeten worden:
    {text}

    Return de klassen in een lijst. Voorbeeld output: ["verzoek datum", "overig", "contact"]. 
    Zorg er voor dat de lijst een lengte van {len(df)} heeft.
    Zorg er voor dat de klassen dezelfde naam behouden. 

    """

    return prompt

def extract_classes(string, classes):
    matched_classes = []
    for class_name in classes:
        pattern = re.escape(class_name)
        matches = [(match.group(), match.start()) for match in re.finditer(pattern, string)]

        if len(matches) > 0:
            matched_classes.extend(matches)
    
    matched_classes.sort(key=lambda x: x[1])  # Sort based on starting index
    return [class_name for class_name, _ in matched_classes]

def run_prompts(df, run_id, path, class_dict, api_option):
    num_rows = len(df)
    batch_size = 5
    max_retries = 3
    classes = ['beslistermijn verdaagd', 'overig', 'contact', 'inwerking treden van Woo', 'verzoek ontvangen', 'verzoek datum', 'ontvangst verzoek bevestigd']


    batches = []

    for i in range(0, num_rows, batch_size):
        retries = 0
        while retries < max_retries:
            try:
                # get start time
                start_time = time.time()
            
                # select rows of batch_size to prompt
                batch = df.iloc[i:i+batch_size]
                # display(batch)

                prompt = get_prompt(batch, class_dict)

                # ask chatgpt
                result = get_completion(prompt)
                # print(f"Raw result: {result}")

                # select result and turn into list
                start_index = result.find('[')
                end_index = result.find(']')
                if start_index != -1:
                    result = result[start_index+1:end_index]
                    result = eval(result)

                else:
                    result = extract_classes(result, classes)

                # print(result)

                # get end time of running batch
                end_time = time.time()
                # print(f"final result:{result}")

              
                # add info to dataframe
                batch = batch.copy()
                batch['batch'] = i//5
                batch['batch_runtime'] = end_time - start_time
                batch['run_id'] = run_id
                batch['prediction'] = result
                batch['prompt'] = prompt              
                    
                
                batches.append(batch)
            
                # uncomment code if using free api:
                if api_option == "free":
                    if end_time-start_time < 30:
                        time.sleep(30 - (end_time-start_time))

                break
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                retries += 1
                
                if api_option == "free":
                    end_time = time.time()
                    if end_time-start_time < 30:
                        time.sleep(30 - (end_time-start_time))
            
            else:
                print("Max retries exceeded. Moving to the next batch.")

    # print("checkpoint to csv")

    df_copy = pd.concat(batches)
    
    if not os.path.exists(path):
        os.makedirs(path)

    filepath = f"{path}predictions.csv"

    if not os.path.isfile(filepath):
        df_copy.to_csv(filepath, index=False)
        # print(f"file created{filepath}")

    else:
        df_csv = pd.read_csv(filepath)
        df_csv = pd.concat([df_csv, df_copy])
        df_csv.to_csv(filepath, index=False)
        # print(f"run of doc added")

    # display(df_copy)
    return None

def run(df,  runs, path, gt, api_option):
    ids = list(set(df['doc_id'].values))

    for i in ids:
        df_doc = df.loc[df['doc_id'] == i]
        # print(f"Doc id: {i} & total dates:{len(df_doc)} & total batches:{len(df_doc)//5} & {ids[0:ids.index(i)+1]}")

        for k in range(runs):
            start_time = time.time()

            # print(f"k original: {k}")
            class_dict = important_tokens(gt)

            run_prompts(df_doc, k, path, class_dict, api_option)

            end_time =  time.time()
            df_time = pd.DataFrame(columns=['doc_id', "run_id", "time"])
            df_time.loc[0] = [i, k, end_time-start_time]

            filepath = f"{path}time.csv"
            if not os.path.isfile(filepath):
                df_time.to_csv(filepath, index=False)
            else:
                df_csv = pd.read_csv(filepath)
                df_csv = pd.concat([df_csv, df_time])
                df_csv.to_csv(filepath, index=False)


# evaluate performance of chatgpt classification of event
def evaluate(df, gt):
    truths = []
    for index, row in df.iterrows():

        # select row in ground truth that matches the current date
        gt_row = gt.loc[(gt['text'] == row['date']) & (gt['doc_id'] == row['doc_id']) & (gt['sentence']==row['sentence']) & (gt['start']==row['start_in_text']) & (gt['end']==row['end_in_text'])]
        
        # if more than one row is selected from the ground truth, this means that the ground truth is not unique
        if len(gt_row) > 1:
            print("error. non unique gt")

        # if no rows get selected that means the date does not have an event
        elif len(gt_row) == 0:
            print("error. missing gt")
            print(row)
        else:
            truths.append(gt_row.iloc[0]['class'])

    # save truths in dataframe
    df_copy = df.copy()
    df_copy['truth'] = truths

    # print out evaluation metrics
    report = classification_report(truths, list(df['prediction'].values))
    print(report)

    # return dataframe with ground truth
    return df_copy

# def average_jaccard_similarity(sentences1, sentences2):
#     nlp = spacy.load("nl_core_news_sm")
#     similarity_scores = []
#     num_pairs = min(len(sentences1), len(sentences2))
    
#     for i in range(num_pairs):
#         doc1 = nlp(sentences1[i])
#         doc2 = nlp(sentences2[i])
        
#         set1 = set(token.text for token in doc1)
#         set2 = set(token.text for token in doc2)
        
#         similarity = len(set1.intersection(set2)) / len(set1.union(set2))
#         similarity_scores.append(similarity)

#     similar_sent = [score for score in similarity_scores if score >= 0.5 ]
#     fraction_50 = len(similar_sent)/len(similarity_scores)
#     similar_sent = [score for score in similarity_scores if score >= 0.75 ]
#     fraction_75 = len(similar_sent)/len(similarity_scores)
#     similar_sent = [score for score in similarity_scores if score >= 1 ]
#     fraction_100 = len(similar_sent)/len(similarity_scores)
#     average = sum(similarity_scores)/len(similarity_scores)
    
#     return average, fraction_50 , fraction_75, fraction_100


# def evaluate(df, gt):
#     truths_class = []
#     comparison = pd.DataFrame(columns=['doc_id','date', 'prediction_class', 'truth', 'sentence'])
#     df_copy = df.copy()
#     for index, row in df.iterrows():
#         truth = False
#         # gt_row = gt.loc[(gt['text'] == row['date']) & (gt['sentence'] == row['sentence']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text'])]
#         gt_row = gt.loc[(gt['text'] == row['date']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text'])]
#         if len(gt_row) > 1:
#             print("error message: more then one match with ground truth")

#         elif len(gt_row) == 1:
#             truth = True

#         comparison.loc[len(comparison.index)] = [row['doc_id'],row['date'], row['prediction_class'], truth, row['sentence']]

#         truths_class.append(truth)

#     report = classification_report(truths_class, list(df['prediction_class'].values))
#     print(report)

#     df_copy['truth'] = truths_class
#     tn, fp, fn, tp = confusion_matrix(truths_class, list(df['prediction_class'].values)).ravel()
#     values = {"fp": fp, "tp":tp, "fn":fn, "tn":tn}
#     print(values)

#     df_sim = df_copy.loc[df_copy['truth'] == True]
#     df_sim = df_sim.loc[~df_sim['prediction_event'].isin(["None", np.nan])]
    


#     truths_events = []
#     for index, row in df_sim.iterrows():
#         gt_row = gt.loc[(gt['text'] == row['date']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text'])]

#         if len(gt_row) == 0:
#             print("error: date missing in gt")
#         elif len(gt_row) > 1:
#             print("error: duplicate rows in gt")
#         else:

#             truths_events.append(gt_row['event'].values[0])


#     df_sim = df_sim.copy()
#     df_sim['truth_event'] = truths_events
#     print(f"Total dates with an event of which ChatGPT extracted an event phrase: {len(df_sim)}")

#     average, fraction_50 , fraction_75, fraction_100 = average_jaccard_similarity(list(df_sim['truth_event'].values), list(df_sim['prediction_event'].values))
#     print(f"Average jaccard similarity: {round(average*100, 3)}% \n Fraction of dates that overlap >= 50%: {round(fraction_50*100, 3)}% \n Fraction of dates that overlap >= 75%: {round(fraction_75*100,3)}% \n Fraction of dates that overlap = 100%: {round(fraction_100*100,3)}% ")
#     return df_copy

# import nltk
# def has_verb(text):
#     try:
#         tokens = nltk.word_tokenize(text)
#         tags = nltk.pos_tag(tokens)
#         for _, tag in tags:
#             if tag.startswith('VB'):
#                 return True
            
#         return False
#     except TypeError:
#         return False
    
# def add_verb_column(df):
#     verb_tokens = ['verzocht', 'bevestigd', 'ingediend', 'vervangen', 'ontvangen', 'verdaagd', 'getreden', 'ingetrokken', 'geïnformeerd', 'betrokken', 'gesteld', 'geven', 'gevraagd', 'maken', 'gesproken', 'gehad']
#     df['verb'] = df['prediction_event'].str.contains('|'.join(verb_tokens))
#     return df
