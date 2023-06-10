from sklearn.model_selection import train_test_split
import pandas as pd
import os

def split(path, train_path, test_path):
    df_doc = pd.read_csv(f"{path}/documents.csv")
    train_doc, test_doc = train_test_split(df_doc, test_size=0.5)

    # get ids of training and test set
    train_ids = list(train_doc['doc_id'].values)
    test_ids = list(test_doc['doc_id'].values)

    # select for each file the documents
    df_combo = pd.read_csv(f"{path}/date_event_combinations.csv")
    train_combo = df_combo.loc[df_combo['doc_id'].isin(train_ids)]
    test_combo = df_combo.loc[df_combo['doc_id'].isin(test_ids)]
    print("combo", len(train_combo), len(test_combo))

    df_corr = pd.read_csv(f"{path}/correction.csv")
    train_corr = df_corr.loc[df_corr['doc_id'].isin(train_ids)]
    test_corr = df_corr.loc[df_corr['doc_id'].isin(test_ids)]
    print("correction", len(train_corr), len(test_corr))

    df_ent = pd.read_csv(f"{path}/entities.csv")
    train_ent = df_ent.loc[df_ent['doc_id'].isin(train_ids)]
    test_ent = df_ent.loc[df_ent['doc_id'].isin(test_ids)]
    print("entities", len(train_ent), len(test_ent))

    df_fd = pd.read_csv(f"{path}/false_dates.csv")
    train_fd = df_fd.loc[df_fd['doc_id'].isin(train_ids)]
    test_fd = df_fd.loc[df_fd['doc_id'].isin(test_ids)]
    print("false dates", len(train_fd), len(test_fd))

    df_rel = pd.read_csv(f"{path}/relations.csv")
    train_rel = df_rel.loc[df_rel['doc_id'].isin(train_ids)]
    test_rel = df_rel.loc[df_rel['doc_id'].isin(test_ids)]
    print("relations", len(train_rel), len(test_rel))

    df_alld = pd.read_csv(f"{path}/all_dates.csv")
    train_dat = df_alld.loc[df_alld['doc_id'].isin(train_ids)]
    test_dat = df_alld.loc[df_alld['doc_id'].isin(test_ids)]
    print("all dates", len(train_dat), len(test_dat))

    # save training set
    if not os.path.exists(f"{train_path}"):
            os.makedirs(f"{train_path}")

    train_combo.to_csv(f"{train_path}/date_event_combinations.csv", index=False)
    train_corr.to_csv(f"{train_path}/correction.csv", index=False)
    train_doc.to_csv(f"{train_path}/documents.csv", index=False)
    train_ent.to_csv(f"{train_path}/entities.csv", index=False)
    train_rel.to_csv(f"{train_path}/relations.csv", index=False)
    train_fd.to_csv(f"{train_path}/false_dates.csv", index=False)
    train_dat.to_csv(f"{train_path}/all_dates.csv", index=False)

    # save test set
    if not os.path.exists(f"{test_path}"):
            os.makedirs(f"{test_path}")

    test_combo.to_csv(f"{test_path}/date_event_combinations.csv", index=False)
    test_corr.to_csv(f"{test_path}/correction.csv", index=False)
    test_doc.to_csv(f"{test_path}/documents.csv", index=False)
    test_ent.to_csv(f"{test_path}/entities.csv", index=False)
    test_rel.to_csv(f"{test_path}/relations.csv", index=False)
    test_fd.to_csv(f"{test_path}/false_dates.csv", index=False)
    test_dat.to_csv(f"{test_path}/all_dates.csv", index=False)

    return None
