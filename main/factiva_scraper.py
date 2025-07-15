# -------------------------------
# PACKAGES
# -------------------------------

import pandas as pd
import os 
import sys
import logging
import csv
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from setup_utils import initialize_and_select_tasks
from scrape_utils import run_scraper_tasks
from datetime import datetime

# ------------------------------- 
# SETTINGS
# -------------------------------

# Dates
start_date = "2014-01-01"
end_date = "2025-07-15"
granularity = "monthly"

# Paths
DROPBOX_ROOT = '/Users/federicopessina/Library/CloudStorage/Dropbox/Work/UCL PhD/Research/Firm_Attention/2. Data'
TASK_FILE_PATH = os.path.join(DROPBOX_ROOT,granularity, "industry_date_grid.csv")
DATA_SAVE_FOLDER = os.path.join(DROPBOX_ROOT, granularity, "factiva_results")

# Parameters 
recreate_tasks = True  # Set to True to recreate the task file

# Industries to scrape
industries = [
    "All",
    "Energy",
    "Transportation/Logistics"
]
# industries = [
#     "All",
#     "Agriculture",
#     "Automotive",
#     "Basic Materials/Resources",
#     "Business/Consumer Services",
#     "Consumer Goods",
#     "Energy",
#     "Financial Services",
#     "Healthcare/Life Sciences",
#     "Industrial Goods",
#     "Leisure/Arts/Hospitality",
#     "Media/Entertainment",
#     "Real Estate/Construction",
#     "Retail/Wholesale",
#     "Technology",
#     "Telecommunication Services",
#     "Transportation/Logistics",
#     "Utilities"
# ]

# Specify subfocuses if needed
subfocuses = [
    "Tariffs",  # Trade barriers/restrictions, under economic news (ecat)
    "Supply Chain"  # Under corporate/industrial news (ccat)
]

# Create log file
log_filename = f"logs/scraper_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# -------------------------------
# INITIALIZE
# -------------------------------

tasks_pending_list, tasks_list = initialize_and_select_tasks(
    TASK_FILE_PATH=TASK_FILE_PATH,
    DATA_SAVE_FOLDER=DATA_SAVE_FOLDER,
    industries=industries,
    subfocuses=subfocuses,
    start_date=start_date,
    end_date=end_date,
    granularity=granularity,
    recreate_tasks=recreate_tasks
)

# --------------------------------------
# START LOOP SCRAPER
# --------------------------------------

first_iteration = True
last_industry = None
last_subfocus = None
    
while True:
    
    if tasks_pending_list.empty:
        print("All tasks completed. Exiting.")
        break
    logging.info(f"Starting scraper tasks for {len(tasks_pending_list)} pending tasks.")
    
    # print("📋 First 5 rows of task file:")
    # print(tasks_list.head())
    
    # Pick first pending task
    current_task = tasks_pending_list.iloc[0]
    industry = current_task['industry']
    subfocus = current_task['subfocus'] if pd.notna(current_task['subfocus']) else None
    task_start_date = current_task['start_date']
    task_end_date = current_task['end_date']
    
    logging.info(f"Running task for industry: {industry} and subfocus: {subfocus}, from {task_start_date} to {task_end_date}")

    # # DEBUG: Print current task details
    # print(f"🔍 DEBUG - Current task:")
    # print(f"  Industry: '{industry}' (type: {type(industry)})")
    # print(f"  Subfocus: '{subfocus}' (type: {type(subfocus)})")
    # print(f"  Start: '{task_start_date}' (type: {type(task_start_date)})")
    # print(f"  End: '{task_end_date}' (type: {type(task_end_date)})")

    # # DEBUG: Check what we're trying to match against
    # subfocus_for_matching = subfocus if subfocus else ""
    # print(f"  Subfocus for matching: '{subfocus_for_matching}'")

    # # DEBUG: Show the exact condition we're using to find this task
    # mask = (
    #     (tasks_list["industry"] == industry) &
    #     (tasks_list["subfocus"] == subfocus_for_matching) &
    #     (tasks_list["start_date"] == task_start_date) &
    #     (tasks_list["end_date"] == task_end_date)
    # )
    # matching_rows = tasks_list[mask]
    # print(f"  Matching rows found: {len(matching_rows)}")
    # if len(matching_rows) > 0:
    #     print(f"  Current status of matching row: {matching_rows.iloc[0]['status']}")

    logging.info(f"Running task for industry: {industry} and subfocus: {subfocus}, from {task_start_date} to {task_end_date}")
    
    # Run task
    try:
        
        # Run task
        run_scraper_tasks(industry,
                          subfocus,
                          task_start_date,
                          task_end_date,
                          last_industry,
                          last_subfocus,
                          first_iteration,
                          DATA_SAVE_FOLDER)
        
         # Update task status to completed 
        if subfocus is None:
            # Match against NaN/null values in the CSV
            mask = (
                (tasks_list["industry"] == industry) &
                (pd.isna(tasks_list["subfocus"])) &  # This matches NaN values
                (tasks_list["start_date"] == task_start_date) &
                (tasks_list["end_date"] == task_end_date)
            )
        else:
            # Match against actual subfocus values
            mask = (
                (tasks_list["industry"] == industry) &
                (tasks_list["subfocus"] == subfocus) &
                (tasks_list["start_date"] == task_start_date) &
                (tasks_list["end_date"] == task_end_date)
            )
        
        print(f"✅ Task completed successfully for {industry}/{subfocus}")
        logging.info(f"✅ Task marked as completed for {industry}/{subfocus}")
        tasks_list.loc[mask, "status"] = 1
        first_iteration = False
        
        # Track last industry to detect change
        last_industry = industry
        last_subfocus = subfocus if subfocus else None
        
    except Exception as e:
        logging.error(f"Error processing task for {industry}/{subfocus} from {task_start_date} to {task_end_date}: {e}", exc_info=True)
         # Add more detailed error info
        print(f"❌ ERROR: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        #logging.error(e)
        # Update task status to failed
        # Update task status to failed - FIXED MATCHING LOGIC
        if subfocus is None:
            mask = (
                (tasks_list["industry"] == industry) &
                (pd.isna(tasks_list["subfocus"])) &
                (tasks_list["start_date"] == task_start_date) &
                (tasks_list["end_date"] == task_end_date)
            )
        else:
            mask = (
                (tasks_list["industry"] == industry) &
                (tasks_list["subfocus"] == subfocus) &
                (tasks_list["start_date"] == task_start_date) &
                (tasks_list["end_date"] == task_end_date)
            )
        
        tasks_list.loc[mask, "status"] = -1
        
    # Save updated task file after each task
    tasks_list.to_csv(TASK_FILE_PATH, index=False)
    print("📁 Task file updated.")
    
     # Refresh task list for next iteration
    tasks_pending_list = tasks_list[tasks_list["status"].isin([0, -1])]
    