# BIN601 Final Project
# Description: Scraping Data from NCBI BioSample Webpages and Visualizing Survey Responses
# Author: Katy Barrett | 23Nov2026


# Import Data

## Import Required Libraries
### Data Handling
import pandas as pd
import csv
#import xlsxwriter                        # Uncomment code if this data output is wanted

### Web Scraping and HTML Parser
import time
import requests
from bs4 import BeautifulSoup

### Data Visualization
import matplotlib.pyplot as plot
import textwrap
import os

## Read in BioSample ID Data
biosam_df = pd.read_csv("biosample_result.txt", header = None, sep = "\t")    # CHANGE WHEN REUSING


# Scrape Data from NCBI BioSample IDs

## Define Variables to use as Parameters for Scraping
### Define random selection of samples (but reproducible) in DataFrame to scrape
my_slice = biosam_df.sample(n = 50, random_state = 31)             # CHANGE WHEN REUSING  

### Define a variable that will store a collection of multiple DataFrames
df_coll = [] 

## Scrape Data
for biosam_id in my_slice.iloc[:, 0]:
    url = f"https://www.ncbi.nlm.nih.gov/biosample/{biosam_id}"
    time.sleep(0.5)                                                # Delay each request in 0.5 second intervals per NCBI polite scraping rules
    
    try:
        res = requests.get(url, timeout = 3)                       # Take 3 seconds to contact webpage before aborting

    except requests.RequestException as e:                         # Print error for scraping failure for specific IDs if applicable
        print(f"Failed for {biosam_id}: {e}")
        continue                   
    
    soup = BeautifulSoup(res.content, "html.parser")               # Define soup variable
    table = soup.find('table')                                     # Define table variable to find and store HTML tagged table
    if table is None:                                              # Print error if table is not found
        print(f"No table found in {biosam_id}")
        continue
    
    rows = table.find_all('tr')                                    # Define rows variable to find and store all data in rows in table
    questions, answers = [], []                                    # Define empty lists for scraped questions and answers in table                                                 
    for row in rows:
        th, td = row.find("th"), row.find("td")  
        if th is None or td is None:                               # Print error if 'th' and 'td' tags are not found
            print(f"No tags found in {biosam_id}")   
            continue                                               
                                                                             
        questions.append(th.get_text(strip = True))                # Append data to eliminate HTML elements from each row in table
        answers.append(td.get_text(strip = True))
    
    ### Write Scraped Data to DataFrame
    surveyData = pd.DataFrame({                                    
        "BioSample_ID": biosam_id,
        'Question': questions,
        'Answer': answers
    })                                                             

    ### Append Data from each Webpage Scrape into DataFrame Collection
    df_coll.append(surveyData)                                     

## Write Tidied Scrape Data to csv
### Concatenate data for export 
total_df = pd.concat(df_coll, ignore_index = True)
total_df.to_csv("biosample_scrape.csv", index = False)

## Optional - Write Tidied Scrape Data to Excel
### Each BioSample DataFrame in df_coll gets a tab in one Excel file
#with pd.ExcelWriter("biosample_scrape.xlsx") as writer:               # Uncomment code if this data output is wanted
    #for df in df_coll:
    #tab_name = str(df["BioSample_ID"].iloc[0])
    #df.to_excel(writer, sheet_name = tab_name, index = False)


# Visualize Survey Response Data

## Plot sex, age category, Clostridioides difficile infection status, and antibiotic history
### Pivot scraped DataFrame into wider format and overwrite duplicate data
wide_total_df = total_df.pivot_table(
    index = "BioSample_ID", columns = "Question", values = "Answer", aggfunc = "first"
)

### Make a list of questions that need graphed
survey_questions = ["sex", "age cat", "cdiff", "antibiotic_history"]         # CHANGE WHEN REUSING

### Include any NA values in the DataFrame if a question in survey_questions does not exist
wide_total_df = wide_total_df.reindex(columns = wide_total_df.columns.union(survey_questions)).fillna("NA")

### Make tidier custom plot titles for each question
plot_titles = {                                                              # CHANGE WHEN REUSING
    "sex": "Sex", 
    "age cat": "Age Category",
    "cdiff": "C. diff Infection Status",
    "antibiotic_history": "Antibiotic History"
}

### Make a directory for the multiple plots that will be exported
os.makedirs("plots", exist_ok = True)

### Loop through latest version of wide_total_df to plot answers to survey_questions
for q in survey_questions:
    
    counts = wide_total_df[q].value_counts()                                   # Count all unique answers in pandas series for each question in survey_questions               

    if "NA" in counts.index:                                                   # Place NA values at the end of each series to ensure it shows last in each plot 
        counts = pd.concat([counts.drop("NA"), counts[["NA"]]])

    fig, ax = plot.subplots(figsize = (8,5))                                   # Create a variable to generate multiple plots: one for each question

    counts.plot(kind = "bar", ax = ax, color = plot.cm.tab10(range(len(counts))), width = 0.8)            # Customize bar plots
    ax.set_title(plot_titles.get(q,q), fontweight = "bold")
    ax.set_xlabel("Respondent Answer")
    ax.set_ylabel("Count")
    ax.set_xticklabels([textwrap.fill(str(l), width = 12) for l in counts.index], rotation = 45)
    ax.margins(x = 0.1, y = 0.1)

    fig.savefig(f"plots/{q.replace(' ', '_')}.png", dpi = 300, bbox_inches = "tight")                     # Save plots to newly made directory with appropriate naming system

plot.show()                                                                                               # Visualize plots in separate matplotlib popup window

### Save filtered data used to generate plots in csv format
plotted_df = wide_total_df[survey_questions].reset_index()                                                
plotted_df.to_csv("plotted_data.csv", index = False)