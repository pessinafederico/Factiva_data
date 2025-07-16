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
from setup_utils import update_task_status
from scrape_utils import run_scraper_tasks
from scrape_utils import init_driver
from datetime import datetime
import time


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
recreate_tasks = False  # Set to True to recreate the task file

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
driver = None

current_task_number = 1
total_tasks = len(tasks_pending_list)
print(f"🚀 Starting scraper with {total_tasks} total tasks")

def reset_browser_state():
    """
    Reset browser state by going back to the original search page
    """
    global driver, first_iteration, last_industry, last_subfocus
    
    try:
        if driver is None:
            logging.info("Driver is None, initializing new driver")
            driver = init_driver()
            first_iteration = True
            last_industry = None
            last_subfocus = None
            return True
            
        # Try to navigate back to the search page
        factiva_url = "https://librarysearch.lse.ac.uk/discovery/fulldisplay?vid=44LSE_INST:44LSE_VU1&tab=Everything&docid=alma99129371110302021&context=L&search_scope=MyInstitution&lang=en"
        
        logging.info("Attempting to navigate back to original page...")
        driver.get(factiva_url)
        time.sleep(5)
        
        # Reset state flags
        first_iteration = True
        last_industry = None
        last_subfocus = None
        
        logging.info("✅ Successfully reset browser state")
        return True
        
    except Exception as e:
        logging.error(f"Failed to reset browser state: {e}")
        
        # If navigation fails, try to quit and reinitialize
        try:
            if driver:
                driver.quit()
                time.sleep(3)
            driver = init_driver()
            first_iteration = True
            last_industry = None
            last_subfocus = None
            logging.info("✅ Successfully reinitialized driver")
            return True
        except Exception as reinit_error:
            logging.error(f"Failed to reinitialize driver: {reinit_error}")
            driver = None
            return False

def handle_task_failure(industry, subfocus, start_date, end_date, error, max_retries=2):
    """
    Handle task failure with retry logic and proper state management
    """
    global current_task_number
    
    logging.error(f"Error processing task for {industry}/{subfocus} from {start_date} to {end_date}: {error}", exc_info=True)
    print(f"❌ ERROR: {error}")
    print(f"❌ Error type: {type(error).__name__}")
    
    remaining_tasks = total_tasks - current_task_number
    print(f"❌ Task {current_task_number}/{total_tasks} FAILED. {remaining_tasks} tasks remaining.")
    
    # Try to reset browser state
    print("🔄 Attempting to reset browser state...")
    if reset_browser_state():
        print("✅ Browser reset successful")
    else:
        print("❌ Browser reset failed - marking task as failed")
        # Update task status to failed
        update_task_status(tasks_list, industry, subfocus, start_date, end_date, -1)
        return False
    
    # Update task status to failed (will be retried if status is -1)
    update_task_status(tasks_list, industry, subfocus, start_date, end_date, -1)
    return True

# Initialize driver once at the start
try:
    driver = init_driver()
    print("✅ Driver initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize driver: {e}")
    logging.error(f"Failed to initialize driver: {e}")
    exit(1)
    
while True:
    if tasks_pending_list.empty:
        print("All tasks completed. Exiting.")
        break
    
    # Pick first pending task
    current_task = tasks_pending_list.iloc[0]
    industry = current_task['industry']
    subfocus = current_task['subfocus'] if pd.notna(current_task['subfocus']) else None
    task_start_date = current_task['start_date']
    task_end_date = current_task['end_date']
    
    logging.info(f"Running task for industry: {industry} and subfocus: {subfocus}, from {task_start_date} to {task_end_date}")
    print(f"🔄 Task {current_task_number}/{total_tasks}: {industry}/{subfocus or 'All'} ({task_start_date} to {task_end_date})")
    logging.info(f"Task {current_task_number}/{total_tasks}: {industry}/{subfocus} {task_start_date}-{task_end_date}")

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
        update_task_status(tasks_list, industry, subfocus, task_start_date, task_end_date, 1)
        
        print(f"✅ Task completed successfully for {industry}/{subfocus}")
        logging.info(f"✅ Task marked as completed for {industry}/{subfocus}")
        remaining_tasks = total_tasks - current_task_number
        print(f"✅ Task {current_task_number}/{total_tasks} completed. {remaining_tasks} tasks remaining.")
        logging.info(f"✅ Task {current_task_number}/{total_tasks} completed")
        
        first_iteration = False
        
        # Track last industry to detect change
        last_industry = industry
        last_subfocus = subfocus if subfocus else None
        
    except Exception as e:
        # Handle the failure
        success = handle_task_failure(industry, subfocus, task_start_date, task_end_date, e)
        
        if not success:
            print("❌ Critical error - cannot continue. Exiting.")
            break
        
    current_task_number += 1
       
    # Save updated task file after each task
    tasks_list.to_csv(TASK_FILE_PATH, index=False)
    print("📁 Task file updated.")
    
    # Refresh task list for next iteration - IMPORTANT: Only get pending tasks (status 0 or -1)
    tasks_pending_list = tasks_list[tasks_list["status"].isin([0, -1])]
    
    # Add a safety check to prevent infinite loops
    if len(tasks_pending_list) == 0:
        print("✅ No more pending tasks. All completed or failed permanently.")
        break

# Clean up
try:
    if driver:
        driver.quit()
        print("✅ Driver cleaned up successfully")
except Exception as e:
    logging.error(f"Error cleaning up driver: {e}")

print("🏁 Scraper finished!")