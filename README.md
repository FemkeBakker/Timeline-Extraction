# Timeline-Extraction-from-decision-letters-using-ChatGPT
This repository contains code for extracting timeline from government decision letters using ChatGPT. 

In this read me you can find the following things:
1. Instruction for the demo 
2. Explanation of the content of the different files
3. Event class definitions
4. Example prompts

### Demo of timeline example
We have marked the annotations of one of the documents in a [PDF](https://github.com/FemkeBakker/Timeline-Extraction/blob/main/demo/example_pdf.pdf) to demonstrated how the annotations look. In [demo.ipynb](https://github.com/FemkeBakker/Timeline-Extraction-from-decision-letters-using-ChatGPT/blob/main/demo.ipynb) we have set up a demonstration, where the notebook takes a document and returns an ordered dataframe as the timeline. As default, we have set up the same document as from the PDF example, however feel free to insert another file as input. More instructions about the demo can be found in demo.ipynb. Below, an image of the timeline we would like the algorithm to return of the document:
<!-- ![image](https://github.com/FemkeBakker/Timeline-Extraction-from-decision-letters-using-ChatGPT/assets/70972237/a209c2ee-c50e-4c5c-b737-94d7623aa3c7) -->
![voorbeeld_timeline3](https://github.com/FemkeBakker/Timeline-Extraction-from-decision-letters-using-ChatGPT/assets/70972237/f98bd4c8-ba98-4a2a-97aa-ef5889cdb7ed)

### Content of the files
- main.ipynb -> notebook where the different steps get connected + evaluated.
- demo.ipynb -> notebook where a demonstration can be run.
- descriptives.md -> descriptive statistics of dataset + predictions of chatGPT
- annotations folder -> folder with data annotated by two annotators, notebook with calculations for Cohen's kappa & annotation guidelines (in Dutch)
- code/run_chatGPT -> notebook that runs the two experiments of ChatGPT
- code/scripts -> contains all files with the code needed to run the algorithm. 
#### data folder
- GT_doccano.jsonl -> original dataset with annotations, downloaded from Doccano (the annotation tool we used).
- data/GT -> contains csv files for the whole, test and trainingset with the ground truth.
- data/preparation -> contains all data needed in preparation stage. In data/preparation/IMIpdfs the original pdfs can be found. 
- data/results -> contains all the results from the steps that needed to be saved in between steps.

### Event class definitions
| Class                        | Description                                                                                                                            | N |
|------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|-----|
| Decision made                | Date on which a decision has been made about the request. It is usually the first date and it is always the date of the letter itself. | 100 |
| Request made                 | Date on which the requester submitted the Woo request.                                                                                 | 95  |
| Request received             | Date on which the request has been received by the government organisation.                                                            | 38  |
| Cofirmation request received | Date on which the government organsation confirmed to the requester that the Woo request has been received.                            | 83  |
| Decision period adjourned    | Date on which the decision period has been adjourned, moved or extended.                                                               | 40  |
| Take effect of Woo           | On 1 may 2020 the Woo took effect and replaced the Wob (former law).                   | 32  |
| Contact                      | Date on which communication took place between two parties.                                                                            | 86  |
| Other                        | Every date that has an event, but does not belong in one of the above-stated classes                                                   | 51  |

### Example prompts
To give an idea about how the prompts looked, we give an example for each of the ChatGPT prompts. The original prompts are in Dutch, but we translated them to English. 
The first prompt is for ChatGPT to extract the event phrase and to classify the dates into dates with an event (True) and without an event (False). The second prompt is for ChatGPT to classify the dates with an event into one of the event classes. The given tokens in the prompts are based on the training set.
#### Prompt 1: Event phrase extraction & date classification (True/False)
![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/6daf7797-1b5b-428a-8614-00479bf12440)
#### Prompt 2: Event classification
![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/c9867caf-5fed-4c55-9007-a4c387d68840)





