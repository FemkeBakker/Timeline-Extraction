import pandas as pd

def remove_false_dates(df, gt):
    print(f"Original length of dataframe:{len(df)}")
    df_copy = df.copy()
    for index, row in df.iterrows():
        gt_row = gt.loc[(gt['text'] == row['date']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text']) & (gt['doc_id'] == row['doc_id']) & (gt['sentence']==row['sentence'])]
        if len(gt_row) > 1:
            print("error: not unique row in ground truth")

        if len(gt_row) == 0:
            df_copy = df_copy.drop(row.name)
   

    print(f"New length after removing mistakes: {len(df_copy)}")
    return df_copy


def remove_no_event_dates(df, gt):
    print(f"Original length of dataframe:{len(df)}")
    df_copy = df.copy()
    for index, row in df.iterrows():
        gt_row = gt.loc[(gt['text'] == row['date']) & (gt['start'] == row['start_in_text']) & (gt['end'] == row['end_in_text']) & (gt['doc_id'] == row['doc_id']) & (row['sentence']==gt['sentence'])]
        
        if len(gt_row) > 1:
            print("error: not unique row in ground truth")

        if len(gt_row) == 0:
            df_copy = df_copy.drop(row.name)

        elif gt_row.iloc[0]['label'] == 'DATE+':
            df_copy = df_copy.drop(row.name)

   

    print(f"New length after removing mistakes: {len(df_copy)}")
    return df_copy