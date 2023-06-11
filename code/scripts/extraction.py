import pandas as pd  
import numpy as np  
import os

""" Function takes the df of a single doccano document and returns a df of all the entities in the document."""
def get_df_entities(df, text):
    entities_df = pd.DataFrame(columns=['id', 'label', 'start', 'end'])

    # make dataframe with id, label, begin and end character of entity
    for entity in df['entities'].values[0]:
        entities_df.loc[len(entities_df.index)] = [entity['id'], entity['label'], entity['start_offset'], entity['end_offset']]

    # add the text to the rows, based on the first and last character
    all_text = [text[row['start']:row['end']] for index, row in entities_df.iterrows()]
    entities_df['text'] = all_text

    return entities_df

""" Function takes the df of a single doccano document and returns a df of all the relations between the entities in the document."""
def get_df_relations(df):
    relations_df = pd.DataFrame(columns=['id', 'from_id', "to_id", "type"])

    for relation in df['relations'].values[0]:
        relations_df.loc[len(relations_df.index)] = [relation['id'], relation['from_id'], relation['to_id'], relation['type']]

    return relations_df

""" Function takes the df of a single doccano document and returns all the info about the doc. """
def extract_info(df):
    text = df['text'].values[0]
    entities_df = get_df_entities(df, text)
    relations_df = get_df_relations(df)

    # check if doc has id labeled, else set doc_id to Nan
    if "ID" in entities_df['label'].values:
        entities_df['doc_id'] = int(entities_df.loc[entities_df['label']=="ID"]['text'].values[0])
        relations_df['doc_id'] = int(entities_df.loc[entities_df['label']=="ID"]['text'].values[0])

    else:
        entities_df['doc_id'] = "None"
        relations_df['doc_id'] = "None"

    dates = entities_df.loc[~entities_df['label'].isin(["event", 'ID', 'title'])]
    dates = dates.sort_values(by=['start'])
    
    return entities_df, relations_df, dates, text

# entities_df, relations_df, dates, text = extract_info(jsonObj)

def add_event(dates_df, relations, entities):
    date_event = dates_df.loc[~dates_df['label'].isin(["DATE+", "date"])]


    # get df with only the date-event relations
    relations_event = relations.loc[relations['type']!= "false-date"]

    # sort relations, so that the first part of an event is always first (date-event, date-event2)
    relations_event = relations_event.sort_values(by=['type'])

    events = []
    begin = []
    end = []
    event_ids = []

    # for every date in date_event add the event to the dataframe
    for index, row in date_event.iterrows():
        id = row['id']
        event = ""
        start = []
        end_char = []
        ids = []

        for index, row2 in relations_event.loc[relations_event['from_id'] == id].iterrows():
            to_id = row2['to_id']

            # add part of event too event variable
            event += " "
            event += entities.loc[entities['id'] == to_id]['text'].values[0]

            # save info of event such as the begin and end characters of the parts and ids of the parts
            start.append(entities.loc[entities['id'] == to_id]['start'].values[0])
            end_char.append(entities.loc[entities['id'] == to_id]['end'].values[0])
            ids.append(entities.loc[entities['id'] == to_id]['id'].values[0])

        
        event = event.strip()
        events.append(event)
        begin.append(start)
        end.append(end_char)
        event_ids.append(ids)

    date_event = date_event.copy()
    date_event['event'] = events
    date_event['event_ids'] = event_ids
    date_event['start_event'] = begin
    date_event['end_event'] = end


    return date_event

"""Function adds sentence of the date to dates_dataframe."""
def add_sentence(dates, text, id):
    # split sentences on newline
    lines = text.split("\n")

    # get start and end character of sentence in original text
    start_positions = []
    end_positions = []
    current_position = 0
    sentence_position = {}
    for line in lines:
        start_positions.append(current_position)
        end_positions.append(current_position + len(line))

        current_position += len(line) + 1


    # add sentence if date start and end character in range of sentence
    sentences = []
    for index, row in dates.iterrows():
        start = row['start']
        end = row['end']

        found = False
        for i in range(len(lines)):
            start_sent = start_positions[i]
            end_sent = end_positions[i]
            sent = lines[i]

            if start >= start_sent and end <= end_sent:
                sentences.append(sent.strip())

    dates['sentence'] = sentences
  
    return dates


""" Function returns a df with all the false dates, including information about relations and corrections to the date"""
def get_false_dates(dates,relations, entities):
    false_dates = dates.loc[dates['label'] == "DATE+"]

    # df with all relations with a fault in labeling
    false_relations = relations.loc[relations['type'] == "false-date"]

    # df with all relations from date to event
    good_relations = relations.loc[relations['type'] != "false-date"]

    # all dates that had a fault in the word labeling: thus 
    label_is_wrong = []
    has_event = []
    right_label = []
    
    for index, row in false_dates.iterrows():
        id = row['id']

        # if DATE+ does not have any relations
        if id not in relations['from_id'].values:
            label_is_wrong.append(False)
            has_event.append(False)
            right_label.append("None")

        else:
            # select new id of corrected date
            new_id = false_relations[false_relations['from_id'] == id]['to_id'].values[0]

            # if date has a relation with an event
            if new_id in good_relations['from_id'].values:
                label_is_wrong.append(True)
                has_event.append(True)
                right_label.append(entities.loc[entities['id'] == new_id]['text'].values[0])

            # if date does not have a relation with an event
            else: 
                label_is_wrong.append(True)
                has_event.append(False)
                right_label.append(entities.loc[entities['id'] == new_id]['text'].values[0])


    false_dates = false_dates.copy()

    false_dates['label_is_wrong'] = label_is_wrong
    false_dates['has_event'] = has_event
    false_dates['right_label'] = right_label
       
    return(false_dates)

def correct_labels(false_dates):
    df = false_dates.loc[false_dates['right_label'] != 'None']

    correct_df = pd.DataFrame(columns=["doc_id", 'right_label', "start", 'end', "parts", "sentence", "start_parts", "end_parts"])

    df = df.sort_values(by=['start'])

    corrections = []
    for index, row in df.iterrows():
        corrections.append((row['right_label'], row['sentence']))


    ids = []
    dates = []
    starts = []
    ends = []
    parts = []
    sentences = []
    start_parts = []
    end_parts = []

    corrections = set(corrections)
    for i in corrections:
        date = i[0]
        sent = i[1]

        dates.append(date)
        sentences.append(sent)

        select = df.loc[(df['right_label'] == date) & (df['sentence'] == sent)]

        ids.append(df['doc_id'].values[0])
        parts.append(list(select['text'].values))
        start_parts.append(list(select['start'].values))
        starts.append(select['start'].values[0])
        end_parts.append(list(select['end'].values))
        ends.append(select['end'].values[-1])

    correct_df["doc_id"] = ids
    correct_df['right_label'] = dates
    correct_df['start'] = starts
    correct_df['end'] = ends
    correct_df['parts'] = parts
    correct_df['sentence'] = sentences
    correct_df['start_parts'] = start_parts
    correct_df['end_parts'] = end_parts

    return correct_df

"""Create dataframe with all dates. Dates have already been corrected if necessary"""
def get_all_dates(date_event, false_dates):
    # Only select dates from false_dates that are not part of date_event combination,
    # since date_event combinations have already been added. 
    fd = false_dates.loc[false_dates['right_label'] == "None"]

    # remove unnecessary columns, add event column
    fd = fd.drop(columns=['label_is_wrong', "has_event", "right_label"])
    fd['event'] = "None"

    # remove unnecessary columns
    df = date_event.drop(columns=['event_ids', 'start_event', "end_event"])

    # combine all dates into df
    df = pd.concat([df,fd])
    
    return df

def get_id_title(entities):
    # check if title was labeled, else return Nan
    if "title" in entities['label'].values:
        title = entities.loc[entities['label'] == "title"]['text'].values[0]
    else: 
        title = "None"

    # check if id was labeled, else return Nan
    if "ID" in entities['label'].values:
        id = int(entities.loc[entities['label'] == 'ID']['text'].values[0])
    else:
        id = "None"

    return title, id

def save_to_csv(date_event, false_dates, docs, path, entities, relations, correction, all_dates):

    if not os.path.exists(path):
        os.makedirs(path)

    date_event.to_csv("{}/date_event_combinations.csv".format(path), index = False)
    false_dates.to_csv("{}/false_dates.csv".format(path), index = False)
    docs.to_csv("{}/documents.csv".format(path), index = False)
    entities.to_csv("{}/entities.csv".format(path), index = False)
    relations.to_csv("{}/relations.csv".format(path), index = False)
    correction.to_csv("{}/correction.csv".format(path), index = False)
    all_dates.to_csv("{}/all_dates.csv".format(path), index = False)

""" Extract information from all documents about date-event combination and false dates. Save in csv files. """
def extract(documents, path):
    date_event = []
    false_dates = []
    entities = []
    relations = []
    correction = []
    all_dates = []
    docs = pd.DataFrame(columns=['doc_id', 'title', 'text'])

    for i in range(len(documents)):
        # make dataframe of single doc
        doc = documents.iloc[[i]]

        # get entities, relations, dates and text
        entities_df, relations_df, dates, text = extract_info(doc)

        entities.append(entities_df)
        relations.append(relations_df)

        # add the title, id and text to dataframe
        title, id = get_id_title(entities_df)
        docs.loc[len(docs.index)] = [id, title, text] 

        # add sentences to dates df
        dates = add_sentence(dates, text, id)

        # make false_dates dataframe
        false_df = get_false_dates(dates, relations_df, entities_df)

        # make date-event combination dataframe
        df_date_event = add_event(dates, relations_df, entities_df)

        # get dataframe of date-event combinations and of false dates
        date_event.append(df_date_event)
        false_dates.append(false_df)
        correction.append(correct_labels(false_df))
        all_dates.append(get_all_dates(df_date_event, false_df))


    # merge all dataframes into one
    entities = pd.concat(entities)
    relations = pd.concat(relations)
    date_event = pd.concat(date_event)
    false_dates = pd.concat(false_dates)
    correction = pd.concat(correction)
    all_dates = pd.concat(all_dates)

    save_to_csv(date_event, false_dates, docs, path, entities, relations, correction, all_dates)
    return None
    
# load doccano file with annotated documents
# jsonObj = pd.read_json(path_or_buf="data/GT21-5.1.jsonl", lines=True)
# extract(jsonObj, "data/GT21-5.1")
