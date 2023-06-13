from filter import filter_and_extract
from sentences_py import load_text, edit_docs

""" Prepare data before annotation """

# filter pdfs based on image- or textbased, using threshold = 0.1
# convert pdf into txt files, save files in IMI_txt_0.1
filter_and_extract("data/preparation/IMIpdfs", "data/preparation/txt_files/IMI_txt_0.1", 0.1)

# filter out sentences that do not have date, 
# save date labels for annotation in data/IMItextclean_0.1
documents, ids = load_text("data/preparation/txt_files/IMI_txt_0.1/")
edit_docs(documents, "data/preparation/IMItextclean_0.1", ids)


