import openai
import os
import pandas as pd
import time
from sklearn.metrics import *
import nltk
import warnings
import numpy as np
from itertools import chain
import json
import spacy
import math
from collections import Counter
import string
import nltk
from nltk.corpus import stopwords

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
    text = ""

    for i in range(len(dates)):
        text += f"{i+1}. Date = {dates[i]}\n"
        text += f"  - sentence = '{sentences[i]}'\n"
    return text

# get list of tokens of string
def tokenize_strings(strings):
    nlp = spacy.load("en_core_web_sm")
    tokenized_list = []
    for string in strings:
        doc = nlp(string)
        tokens = [token.text for token in doc]
        tokenized_list.extend(tokens)
    return tokenized_list

# remove stopwords from list of tokens
def remove_stopwords(tokens):
    stop_words = set(stopwords.words('dutch'))
    # remove dutch stopwords
    
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
    # remove tokens that exist out of 1 character
    filtered_tokens = [token for token in filtered_tokens if len(token) > 1]
    return filtered_tokens

# select keys where the value is higher or equal to the threshold
def get_keys_above_threshold(dictionary, threshold):
    return [key for key, value in dictionary.items() if value >= threshold]

# get a list of verb tokens from a list of sentences
def extract_verbs(sentences):
    nlp = spacy.load("nl_core_news_sm")
    verb_tokens = []
    for sentence in sentences:
        doc = nlp(sentence)
        verb_tokens.extend([token.text for token in doc if token.pos_ == 'VERB'])
    return verb_tokens

# select most important verbs in event phrases
def verb_tokens(gt_original):
    # get list of event phrases from ground truth
    gt = gt_original.loc[gt_original['class'] != 'besluit datum']
    gt_true = gt.loc[gt['label'] != "DATE+"]
    class_dict = dict()
    events = list(gt_true['event'].values)

    # get the verbs
    tokens = extract_verbs(events)

    # remove punctuation
    tokens = [token for token in tokens if token not in string.punctuation]

    # remove stopwords
    tokens = remove_stopwords(tokens)  

    # select top verbs  
    important = get_keys_above_threshold(Counter(tokens), math.ceil(len(gt_true)/60))
    class_dict["True"] = important
    return class_dict

# put together prompts
def get_prompt(df, class_dict):
    dates = list(df['date'].values)
    sentences = list(df['sentence'].values)
    text = ask_sentences(dates, sentences)


    ex_class =['True', 'False','True', 'False', 'False']
    ex_event = ["beslistermijn is met vier weken verdaagd", "None", "vraagt u om de stand van zaken", "None", "None"]
    
    prompt = f"""
Gegeven de volgende zinnen en datums, voer twee taken uit:
- Taak 1: Vind de beschrijving van de gebeurtenis in de zin voor de betreffende datum. 
De gebeurtenisomschrijving zijn woorden in de zin die beschrijven wat er op die datum is gebeurd.
- Taak 2: Classificeer de datum op basis van de gebeurtenisomschrijving in twee klassen: "True" en "False". 
Volg deze stappen om de datums te classificeren:
1. Check of de datum een gebeurtenis omschrijving heeft.
2. Als de datum geen gebeurtenis omschrijving heeft, classificeer dan de datum als "False".
3. Als de datum wel een gebeurtenis omschrijving heeft, check dan of minimaal één woord ook voorkomt in de lijst met tokens: {class_dict['True']}.
4. Als er geen enkel woord in de gebeurtenis omschrijving voorkomt in de lijst met tokens, classificeer dan de datum als "False".
5. Als er 1 of meerdere woorden in de gebeurtenis omschrijving voorkomen in de lijst met tokens, classificeer dan de datum als "True".

Dit zijn de {len(df)} datums dit waarop de taken uitgevoerd moeten worden:
{text}

Retourneer het resultaat als een JSON-bestand.
Het JSON-bestand bevat 2 keys: gebeurtenis_omschrijving en classificatie.
Geef voor elke key een lijst met de voorspellingen. Zorg er voor dat de lijsten een lengte van {len(df)} hebben.
Als de gebeurtenis omschrijving ontbreekt van een datum, geef dan "None". 
Zorg er voor dat alles in lijsten tussen aanhalingstekens staat. 
Voorbeeld output:
- "classificatie" = {ex_class[0:len(df)]}
- gebeurtenis_omschrijving = {ex_event[0:len(df)]}

    """
    return prompt

    
# extract the predictions of chatGPT
def extract_result(prompt_result):
    events = prompt_result['gebeurtenis_omschrijving']
    classes = prompt_result['classificatie']
    return events, classes

# for each document run prompt
def run_prompts(df, run_id, path, class_dict, api_option):
    num_rows = len(df)
    batch_size = 5
    max_retries = 3
    classes = ['True', 'False']
    batches = []

    # split dates of document in batches of 5, meaning max 5 dates per prompt
    for i in range(0, num_rows, batch_size):
        retries = 0
        while retries < max_retries:
            # get start time of batch
            start_time = time.time()

            # chatgpt can be buggy, sometimes server overloaded.
            try:             
            
                # select rows of batch_size to prompt
                batch = df.iloc[i:i+batch_size]

                # get prompt
                prompt = get_prompt(batch,  class_dict)

                # ask chatgpt
                result = get_completion(prompt)

                try:
                    # try to extract result
                    data = json.loads(result)
                    events, classes = extract_result(data)
                    batch = batch.copy()
                    batch.loc[:,'prediction_event'] = events
                    batch.loc[:,'prediction_class'] = classes


                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    print(result)
                    batch = batch.copy()
                    batch['prediction_event'] = "None"
                    batch['prediction_class'] = "None"

                # get end time of running batch
                end_time = time.time()

                # add info to dataframe
                batch = batch.copy()
                batch['batch'] = i//5
                batch['batch_runtime'] = end_time - start_time
                batch['run_id'] = run_id
                batch['prompt'] = prompt
                batches.append(batch)

                # uncomment code if using free api:
                if api_option == 'free':
                    if end_time-start_time < 30:
                        time.sleep(30 - (end_time-start_time))
                break
            except Exception as e:
                print(f"An error occurred: {str(e)}")
                retries += 1
                # uncomment code if using free api:
                if api_option == 'free':
                    end_time = time.time()
                    if end_time-start_time < 30:
                        time.sleep(30 - (end_time-start_time))
            
            else:
                print("Max retries exceeded. Moving to the next batch.")
    
    # combine all batches into one dataframe
    df_copy = pd.concat(batches)
    
    if not os.path.exists(path):
        os.makedirs(path)

    filepath = f"{path}predictions.csv"

    # add dataframe to csv.
    if not os.path.isfile(filepath):
        df_copy.to_csv(filepath, index=False)
        # print(f"file created{filepath}")

    else:
        df_csv = pd.read_csv(filepath)
        df_csv = pd.concat([df_csv, df_copy])
        df_csv.to_csv(filepath, index=False)
    return None

# run chatgpt for all documents
def run(df, runs, path, gt, api_option):
    ids = list(set(df['doc_id'].values))

    for i in ids[0:1]:
        df_doc = df.loc[df['doc_id'] == i]
        # print(f"Doc id: {i} & total dates:{len(df_doc)} & total batches:{len(df_doc)//5} & {ids[0:ids.index(i)+1]}")

        for k in range(runs):
            start_time = time.time()

            # print(f"k original: {k}")

            # get import verbs
            class_dict = verb_tokens(gt)
            
            # run the prompts
            run_prompts(df_doc, k, path, class_dict, api_option)

            # get runtime of a whole document
            end_time =  time.time()
            df_time = pd.DataFrame(columns=['doc_id', "run_id", "time"])
            df_time.loc[0] = [i, k, end_time-start_time]

            # save runtime of a document in file
            filepath = f"{path}time.csv"
            if not os.path.isfile(filepath):
                df_time.to_csv(filepath, index=False)
            else:
                df_csv = pd.read_csv(filepath)
                df_csv = pd.concat([df_csv, df_time])
                df_csv.to_csv(filepath, index=False)

# evaluate performance of chatgpt classification of event
# def evaluate(df, gt):
#     truths = []
#     for index, row in df.iterrows():

#         # select row in ground truth that matches the current date
#         gt_row = gt.loc[(gt['text'] == row['date']) & (gt['doc_id'] == row['doc_id']) & (gt['sentence']==row['sentence']) & (gt['start']==row['start_in_text']) & (gt['end']==row['end_in_text'])]
        
#         # if more than one row is selected from the ground truth, this means that the ground truth is not unique
#         if len(gt_row) > 1:
#             print("error. non unique gt")

#         # if no rows get selected that means the date does not have an event
#         elif len(gt_row) == 0:
#             print("error. missing gt")
#             print(row)
#         else:
#             truths.append(gt_row.iloc[0]['class'])

#     # save truths in dataframe
#     df_copy = df.copy()
#     df_copy['truth'] = truths

#     # print out evaluation metrics
#     report = classification_report(truths, list(df['prediction'].values))
#     print(report)

#     # return dataframe with ground truth
#     return df_copy

def average_jaccard_similarity(sentences1, sentences2):
    nlp = spacy.load("nl_core_news_sm")
    similarity_scores = []
    num_pairs = min(len(sentences1), len(sentences2))
    
    for i in range(num_pairs):
        doc1 = nlp(sentences1[i])
        doc2 = nlp(sentences2[i])
        
        set1 = set(token.text for token in doc1)
        set2 = set(token.text for token in doc2)
        
        similarity = len(set1.intersection(set2)) / len(set1.union(set2))
        similarity_scores.append(similarity)

    similar_sent = [score for score in similarity_scores if score >= 0.5 ]
    fraction_50 = len(similar_sent)/len(similarity_scores)
    similar_sent = [score for score in similarity_scores if score >= 0.75 ]
    fraction_75 = len(similar_sent)/len(similarity_scores)
    similar_sent = [score for score in similarity_scores if score >= 1 ]
    fraction_100 = len(similar_sent)/len(similarity_scores)
    average = sum(similarity_scores)/len(similarity_scores)
    
    return average, fraction_50 , fraction_75, fraction_100

def evaluate(df, gt):
    truths_class = []
    comparison = pd.DataFrame(columns=['doc_id','date', 'prediction_class', 'truth', 'sentence'])
    df_copy = df.copy()
    for index, row in df.iterrows():
        truth = False
        # gt_row = gt.loc[(gt['text'] == row['date']) & (gt['sentence'] == row['sentence']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text'])]
        gt_row = gt.loc[(gt['text'] == row['date']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text'])]
        if len(gt_row) > 1:
            print("error message: more then one match with ground truth")

        elif len(gt_row) == 1:
            truth = True

        comparison.loc[len(comparison.index)] = [row['doc_id'],row['date'], row['prediction_class'], truth, row['sentence']]

        truths_class.append(truth)

    report = classification_report(truths_class, list(df['prediction_class'].values))
    print(report)

    df_copy['truth'] = truths_class
    tn, fp, fn, tp = confusion_matrix(truths_class, list(df['prediction_class'].values)).ravel()
    values = {"fp": fp, "tp":tp, "fn":fn, "tn":tn}
    print(values)

    df_sim = df_copy.loc[df_copy['truth'] == True]
    df_sim = df_sim.loc[~df_sim['prediction_event'].isin(["None", np.nan])]
    


    truths_events = []
    for index, row in df_sim.iterrows():
        gt_row = gt.loc[(gt['text'] == row['date']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text'])]

        if len(gt_row) == 0:
            print("error: date missing in gt")
        elif len(gt_row) > 1:
            print("error: duplicate rows in gt")
        else:

            truths_events.append(gt_row['event'].values[0])


    df_sim = df_sim.copy()
    df_sim['truth_event'] = truths_events
    print(f"Total dates with an event of which ChatGPT extracted an event phrase: {len(df_sim)}")

    average, fraction_50 , fraction_75, fraction_100 = average_jaccard_similarity(list(df_sim['truth_event'].values), list(df_sim['prediction_event'].values))

    print(f"Average jaccard similarity: {round(average*100, 3)}% \n Fraction of dates that overlap >= 50%: {round(fraction_50*100, 3)}% \n Fraction of dates that overlap >= 75%: {round(fraction_75*100,3)}% \n Fraction of dates that overlap = 100%: {round(fraction_100*100,3)}% ")
    return df_copy, df_sim