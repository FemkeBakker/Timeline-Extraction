# Descriptives
Here we show descriptives of the test set, which contains 50 documents. In figure 1 the distribution of the classes can be seen. Furthermore, Figure 2 contains the distribution of token length of the sentences. What we can see in Fig. 1 is that all documents have a "decision made" date, but not a "request made" date. This because there are documents which only state the "request received" date. Furthermore, in Fig. 2 we can see that the token length of the sentences can differ a lot.

![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/4576ca7f-0d76-42d3-9e71-cd5ef60db33e) ![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/e620b1b2-1657-4a15-805e-97db1e33c32e)

Now, we will dive a little deeper into the predictions of the algorithm. First, we will show the distribution over the amount of sentences that contain at least one date with an event. This distribution is taken from the after date-correction step and the mistakes that have been during this step has been removed (dataset that is the input for the first chatGPT prompt). There are a total of 399 sentences in this dataset, of which 193 sentences contain at least one date with an event.  As shown in Fig 3. most sentences contain only one date with an event. However, 15.5% (30 sentences) contains more than one date of which at least one date with an event. In Fig 4. we can see the distribution of the date-event phrase matching of those 30 sentences, which contain in total 67 dates.  

![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/ea86461e-1683-4f4d-a737-63c433baa62e) ![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/54d500ff-bc37-4df3-9f02-8034e6e3bea7)

Next, we will take a look at the predicted event phrases by chatGPT. There were 144 dates with an event in the ground of which ChatGPT also extracted an event phrase. ChatGPT did not extract an event phrase from the other dates with an event. Fig 5. shows the unique token length of the event phrases from the ground truth. We selected the same 144 dates with an event which ChatGPT predicted. Fig 6. shows the unique token length of the predictions of ChatGPT for dates with an event. We found that 13 of the 144 event phrase overlap 100% with the unqiue tokens in the ground truth. Most of the event phrases (81, 56%) that do not overlap 100% contain extra words in the prediction that are not in the ground truth. Thus, these predictions are too long. There are 50 event phrase predictions that do not have any extra words that are not in the ground truth, but do miss words from the ground truth. Thus, these predictions are too short. 

![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/2b825220-f50d-484a-abd6-bc9c4882485b) ![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/beef30ce-7f6e-438b-93ed-45728b7a30e6)

Then, we would also like to compare the predictions of the event-classes and the ground truth. Fig 1. already shows the distribution of the classes in the ground truth. A difference we can see is that more dates were classified as "request made" and less dates have been classified as "request received" as in the ground truth. 

![image](https://github.com/FemkeBakker/Timeline-Extraction/assets/70972237/96280320-274a-47c0-921e-7cfe3629867c)







