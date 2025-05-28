# -------------------------------
# PACKAGES
# -------------------------------

import pandas as pd
import os 
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from setup_utils import initialize_and_select_tasks
from scrape_utils import run_scraper_tasks

# ------------------------------- 
# SETTINGS
# -------------------------------

# Paths (customize as needed)
DROPBOX_ROOT = '/Users/federicopessina/Library/CloudStorage/Dropbox/Work/UCL PhD/Research/Firm_Attention/2. Data'
TASK_FILE_PATH = os.path.join(DROPBOX_ROOT, "industry_date_grid.csv")
DATA_SAVE_FOLDER = os.path.join(DROPBOX_ROOT, "factiva_results")

# Configuration
industries = [
    "Agriculture",
    "Automotive",
    "Basic Materials/Resources",
    "Business/Consumer Services",
    "Consumer Goods",
    "Energy",
    "Financial Services",
    "Healthcare/Life Sciences",
    "Industrial Goods",
    "Leisure/Arts/Hospitality",
    "Media/Entertainment",
    "Real Estate/Construction",
    "Retail/Wholesale",
    "Technology",
    "Telecommunication Services",
    "Transportation/Logistics",
    "Utilities"
]

start_date = "2014-01-01"
#end_date = "2025-05-01"
end_date = "2014-01-15"
granularity = "weekly"

# -------------------------------
# INITIALIZE
# -------------------------------

tasks_pending_list, tasks_list = initialize_and_select_tasks(
    TASK_FILE_PATH=TASK_FILE_PATH,
    DATA_SAVE_FOLDER=DATA_SAVE_FOLDER,
    industries=industries,
    start_date=start_date,
    end_date=end_date,
    granularity=granularity
)

# --------------------------------------
# START LOOP SCRAPER
# --------------------------------------


first_iteration = True
last_industry = None
    
while True:
    
    if tasks_pending_list.empty:
        print("All tasks completed. Exiting.")
        break
    print(f"Starting scraper tasks for {len(tasks_pending_list)} pending tasks.")
    
    # Pick first pending task
    current_task = tasks_pending_list.iloc[0]
    industry = current_task['industry']
    start_date = current_task['start_date']
    end_date = current_task['end_date']
    
    print(f"Running task for industry: {industry}, from {start_date} to {end_date}")
    
    # Run task
    try:
        # Run task
        run_scraper_tasks(industry,
                          start_date,
                          end_date,
                          last_industry,
                          first_iteration,
                          DATA_SAVE_FOLDER)
        # Update task status to completed
        tasks_list.loc[
            (tasks_list["industry"] == industry) &
            (tasks_list["start_date"] == start_date) &
            (tasks_list["end_date"] == end_date), "status"] = 1
        first_iteration = False
        # Track last industry to detect change
        last_industry = industry
        
    except Exception as e:
        print(e)
        # Update task status to failed
        tasks_list.loc[
            (tasks_list["industry"] == industry) &
            (tasks_list["start_date"] == start_date) &
            (tasks_list["end_date"] == end_date), "status"] = -1
        
    # Save updated task file after each task
    tasks_list.to_csv(TASK_FILE_PATH, index=False)
    print("📁 Task file updated.")
    
     # Refresh task list for next iteration
    tasks_pending_list = tasks_list[tasks_list["status"].isin([0, -1])]
    