# Timeline-Extraction-from-decision-letters-using-ChatGPT
This repository contains code for extracting timeline from government decision letters using ChatGPT. 

In this read me you can find the following things:
1. Instruction for the demo
2. Explanation of the content of the different files
3. Example prompts

### Demo of timeline example
We have marked the annotations of one of the documents in a [PDF](https://github.com/FemkeBakker/Timeline-Extraction-from-decision-letters-using-ChatGPT/blob/main/voorbeeld_pdf.pdf) to demonstrated how the annotations look. In [demo.ipynb](https://github.com/FemkeBakker/Timeline-Extraction-from-decision-letters-using-ChatGPT/blob/main/demo.ipynb) we have set up a demonstration, where the notebook takes a document and returns an ordered dataframe as the timeline. As default, we have set up the same document as from the PDF example, however feel free to insert another file as input. More instructions about the demo can be found in demo.ipynb. Below, an image of the timeline we would like the algorithm to return of the document:
<!-- ![image](https://github.com/FemkeBakker/Timeline-Extraction-from-decision-letters-using-ChatGPT/assets/70972237/a209c2ee-c50e-4c5c-b737-94d7623aa3c7) -->
![voorbeeld_timeline3](https://github.com/FemkeBakker/Timeline-Extraction-from-decision-letters-using-ChatGPT/assets/70972237/f98bd4c8-ba98-4a2a-97aa-ef5889cdb7ed)

### Content of the files
- main.ipynb -> notebook where the different steps get connected + evaluated.
- demo.ipynb -> notebook where a demostration can be run.
- code/descriptives.ipynb -> notebook with descriptive statistics of dataset + predictions of chatGPT
- code/run_chatGPT -> notebook that runs the two experiments of ChatGPT
- code/scripts -> contains all files with the code needed to run the algorithm. 
#### data folder
- GT_doccano.jsonl -> original dataset with annotations, downloaded from Doccano (the annotation tool we used).
- data/GT -> contains csv files for the whole, test and trainingset with the ground truth.
- data/preparation -> contains all data needed in preparation stage. In data/preparation/IMIpdfs the original pdfs can be found. 
- data/results -> contains all the results from the steps that needed to be saved in between steps.

### Example prompts
To give an idea about how the prompts looked, we give an example for each of the ChatGPT prompts. The original prompts are in Dutch, but we translated them to English. 
The first prompt is for ChatGPT to extract the event phrase and to classify the dates into dates with an event (True) and without an event (False). 




