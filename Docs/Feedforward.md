# Project Information

**FIRST & LAST NAME:** Marius Cezar Sirbu  
**Sparring Partner:** Dobrescu Rares Andrei  
**Project Summary:** Material Identification | Smart Trash Bin  
**Project Title:** The SmartBin

# Tips for Feedback Conversations

## Preparation

> I would like to have my project run very efficiently. Git feedback will be really needed.
> Electronics: I need to manage the power input for the stepper motor externally, I would want to have good power management as well as good component management
> Maker Design Skills - What specific methods can I use for a specific type of wood etching?

## During the Conversation:

> **Listen actively:** Do not immediately go on the defensive but try to listen well. Show both verbally and non-verbally that you are paying attention to the feedback by maintaining an open posture (eye contact, upright posture), taking notes, nodding...

> **Take notes:** Write down the feedback so you have it later. Note the key words and find a quick notation method for yourself. If you take good notes, you can briefly review your main feedback points at the end of the conversation.

> **Summarize:** Do not wait for a summary from the instructors, this is your task: Check if you have understood the message correctly by actively listening and summarizing in your own words.

> **Think about it:** Consider what you are going to do with the feedback and follow up. Do you find the comments justified or unjustified? Do you recognize yourself in the feedback? How are you going to address this?

## AFTER THE CONVERSATION

> Reread your notes and create action points. Make choices from all the feedback you received: What can you work on and what will you set aside for now. What were the priorities? Review the assignment sheet again to determine your focus points. Write your action points on the feedback sheet.

# Feedforward Conversations

## Conversation 1 (Date: 29/05/2024)

Lecturer: Tijn 

### Questions for this conversation: 

- ***Question 1:*** What technique should I choose to shape a part of my maker part?
- ***Question 2:*** What is  the capacity of the laser cutter in terms of dimensions of the wood that can be processed?
- ***Question 3:*** How can I choose the right gearing for the moving part?
- ***Question 4:*** Are the electronics I have chosen suitable for the weight/complexity of the prototype?

### This is the feedback on my questions.

- ***Feedback 1:*** I should use the fixed drill for creating the semi-holes. When I create the svg files, don't forget to etch the shape.
- ***Feedback 2:*** 600x450mm for wood. I should either scale down my prototype so the pieces fit in the small CNC, or use the industrial CNC(needs assistance/gets pretty busy).
- ***Feedback 3:*** I should first choose one of the 2 gears to laser cut out of acryl, and the other one shall be wooden so I can apply the modifications in sizing if needed. Use gear generator softwares for getting the right dimensions, ratios, sizing.
- ***Feedback 4:*** My electronic components seem to fit well the task I want to assign them to.

## Conversation 2 (Date: 03/06/2024)

Lecturer: Pieter Jan

### Questions for this conversation:
- **Fixed the Github lfg problem**
- ***Question 1:*** What would be the best way to implement the transmission mechanism between the stepper motor and the gearing?

### This is the feedback on my questions.

- ***Feedback 1:*** I should make a hole in the layer between the stepper motor and the gear, and then3D print a platform according to the right sizing needed to avoid design and mechanical complications.

## Conversation 3 (Date: 06/06/2024)

Lecturer: Geert

Questions for this conversation:

- Question 1: Where can I solder my circuit components?
- Question 2: Check availability of some resistors and power adapters to know what to choose.(DC power adapter, female dc power connector, 10k ohm resistors

This is the feedback on my questions.

- Feedback 1: A.1.102 in the presence of either Geert or Pieter-Jan
- Feedback 2: I don't need to get resistors because the RasPi already has built in resistors in the power pins.
- Feedback 3; I got a comprehensive guide for connecting the electronics correctly.


## MVP Tour moments:

**28 May:**

- I should train the model locally and fine-tune it. Add more epochs.
- Add less preprocessing features and more augmentation features.
- Correctly format the MD file.
- Establish the connection between the laptop and the RasPi

**4 June**

- Update the feedforward file accordingly.
- Schedule consult with Marie to talk about the model accuracy.
- Update the logic of the workflow, remove unneeded parts

**11 June**

- Add a color indication for the user when the bin is available to be used in the right compartment.
- Start with the documentation files. (Video/Instructables/Poster)
- Add build progress to toggl.

---

### AI Development:

**24 May**  
- Analyzed the possibilities of training the dataset solely by classification.  
- Determined this approach will not work as an initial object identification model is needed to crop the bounding box before inputting it into the classification model.

**27 May**  
- Created the dataset for the object identficiation model, annotated data that was mislabeled.  
- Tried the model through the api in VScode. It is functional, but the dataset neeeds more annotations, as well as the model has to be trained locally.

**28 May**  
- The object detection model has been trained in 10 epochs, achieving the best R2 score of 0.82
- The classification model has been trained achiueving a 50% validation result.

**29 May**
- Applied Hyperparameter Tuning to the classification model using RandomSearch with cross validation
- Manually labeled all the dataset with the smart polygon tool on roboflow, retrained a MaskRCNN model, because YOLO - no matter of the optimization applied, does not offer a higher validation score than 0.54.

**30 May**

- Created a new version of the dataset with 100% correct annotations and labels and trained the yolo model again for 20 epochs.

- Validation results:

    | Class | Images | Instances | Box(P) |   R   | mAP50 | mAP50-95 |
    |-------|--------|-----------|--------|-------|-------|----------|
    | all   | 225    | 238       | 0.76   | 0.866 | 0.831 | 0.789    |
    | Glass | 57     | 59        | 0.788  | 0.898 | 0.86  | 0.784    |
    | PMD   | 83     | 84        | 0.857  | 0.854 | 0.922 | 0.899    |
    | Paper | 72     | 81        | 0.897  | 0.858 | 0.881 | 0.85     |
    | Rest  | 13     | 14        | 0.499  | 0.853 | 0.662 | 0.624    |

  
**31 May**
  - Start of extensive fine-tuning of the model.

 **2 June**
  - Finished fine-tuning the model. Achieving way better accuracy on the testset and overall robustness.

**7 June**

- Trained another 2nd model just for classification purposes. Achieving way better results in all kind of lighting conditions.
    
---
### Code:

**31 May**

- Started creating the code files for the model prediction to be output to the RasPi.


**3 June**

- Created the format that sends the right type of data between the model and the RasPi.
- Added the functionality of adding made predictions to the CSV file so the RasPi understands the position of the bin no matter the point the program is started at.
- Established the full workflow on the RasPi. Initialization -> Camera -> Classification -> Output.

  
**7 June**
- Electriconics workflow ready. Power BTN -> Scan Button -> Stepper Motor. All steps are accompanied by indications on the LCD display and he RGB led.
- The code reads the last used bin to understand how to manipulate the position of the stepper motor according to the present prediction.

___
### Build Progress:

**24 May**  
- Completed the list of materials with accurate sizing for each item.  
- Awaiting delivery to commence the build process step-by-step.

**27 May**
- Finalized the life-scaled 3D design on Tinkercad
- Started creating the .svg illustrator files for the CNC machine.

**31 May**
- Placed the order for all the electronic components needed.

**4 June**
- Received the electronics and other components, started assembly.


