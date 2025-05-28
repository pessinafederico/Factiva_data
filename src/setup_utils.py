import os
import pandas as pd
from datetime import timedelta, datetime

def generate_date_ranges(start_date, end_date, freq):
    """
    Generates date ranges based on the specified frequency.
    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
        freq (str): Frequency of the date ranges ('monthly', 'quarterly', 'weekly').
    Returns:
        list: List of tuples containing start and end dates for each range.
    """
    
    ranges = []
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    if freq == "monthly":
        dates = pd.date_range(start, end, freq="MS")
    elif freq == "quarterly":
        dates = pd.date_range(start, end, freq="QS")
    elif freq == "weekly":
        dates = pd.date_range(start, end, freq="W-MON") 
    else:
        raise ValueError("Unsupported frequency")

    for i in range(len(dates) - 1):
        ranges.append((dates[i].strftime("%Y-%m-%d"), dates[i + 1].strftime("%Y-%m-%d")))
    return ranges

def initialize_and_select_tasks(
    TASK_FILE_PATH,
    DATA_SAVE_FOLDER,
    industries,
    start_date,
    end_date,
    granularity
):
    '''
    Initializes the task file and selects tasks for processing.
    Args:
        TASK_FILE_PATH (str): Path to the task file.
        DATA_SAVE_FOLDER (str): Folder to save the results.
        industries (list): List of industries to process.
        start_date (str): Start date for tasks in 'YYYY-MM-DD' format.
        end_date (str): End date for tasks in 'YYYY-MM-DD' format.
        granularity (str): Granularity of the tasks ('monthly', 'quarterly', 'weekly').
    Returns:
        tuple: Selected tasks DataFrame, full task DataFrame, and industry folder path.
    '''
    # -------------------------------
    # CREATE TASK FILE IF NOT EXISTS
    # -------------------------------
    if os.path.exists(TASK_FILE_PATH):
        print(f"Task file already exists: {TASK_FILE_PATH}")
    else:
        print(f"Creating task file: {TASK_FILE_PATH}")
        date_ranges = generate_date_ranges(start_date, end_date, granularity)

        records = []
        for industry in industries:
            for (start, end) in date_ranges:
                records.append({
                    "industry": industry,
                    "start_date": start,
                    "end_date": end,
                    "status": 0
                })

        df = pd.DataFrame(records)
        df.to_csv(TASK_FILE_PATH, index=False)
        print(f"Saved {len(df)} tasks to: {TASK_FILE_PATH}")

    # Ensure save folder exists
    os.makedirs(DATA_SAVE_FOLDER, exist_ok=True)
    print(f"Output directory ready: {DATA_SAVE_FOLDER}")

    # -------------------------------
    # EXTRACT TASKS 
    # -------------------------------
    tasks_list = pd.read_csv(TASK_FILE_PATH)
    
    # Keep all tasks that are not done (status != 1)
    tasks_pending_list = tasks_list[tasks_list["status"] != 1]
    
    # -------------------------------- 
    # Print number of tasks remaining by industry with a total at the end
    # --------------------------------
    if tasks_pending_list is not None:
        tasks_remaining = tasks_pending_list.groupby("industry").size().reset_index(name='remaining_tasks')
        print("Remaining tasks by industry:")
        print(tasks_remaining)

    if tasks_pending_list.empty:
        print("✅ All tasks completed.")
        return None, tasks_list, None
    else:
        print(f"🛠️  {len(tasks_pending_list)} total tasks pending or failed.")
        
    # -------------------------------- 
    # Create industry folder paths
    # -------------------------------- 
    for industry in industries: 
        industry_folder = os.path.join(DATA_SAVE_FOLDER, industry.replace("/", "_"))
        if not os.path.exists(industry_folder):
            os.makedirs(industry_folder)

    return tasks_pending_list, tasks_list