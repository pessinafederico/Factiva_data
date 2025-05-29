import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import os
import csv
import logging

driver = None

# Define function to wait for an element to be clickable
def wait_and_get_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )

# Define function to initialize the Selenium WebDriver
def init_driver():
    global driver
    if driver is not None:
        return driver
    
    chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    user_data_dir = "/Users/federicopessina/ChromeProfile"
    remote_debugging_port = "9222"
    factiva_url = "https://librarysearch.lse.ac.uk/discovery/fulldisplay?vid=44LSE_INST:44LSE_VU1&tab=Everything&docid=alma99129371110302021&context=L&search_scope=MyInstitution&lang=en"

    logging.info("Launching Chrome browser with remote debugging...")
    subprocess.Popen([
        chrome_path,
        f"--remote-debugging-port={remote_debugging_port}",
        f"--user-data-dir={user_data_dir}",
        factiva_url
    ])
    logging.info("Chrome launched. Log in manually, then press Enter to continue...")
    input()

    options = Options()
    options.add_experimental_option("debuggerAddress", "localhost:9222")
    # Suppress logs
    options.add_argument("--log-level=3")  # ERROR level
    options.add_argument("--silent")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # Set service with suppressed output
    logging.info("Setting up ChromeDriver service...")
    service = Service("/opt/homebrew/bin/chromedriver", log_path=os.devnull, log_output=os.devnull)
    driver = webdriver.Chrome(service=service, options=options)
    logging.info("Connected to ChromeDriver via remote debugging.")

    time.sleep(3)
    return driver

# Define function to change the date range
def change_date_range(driver, start_date, end_date):
    '''
    Change the date range in the Factiva search interface.
    
    Args:
        driver (webdriver): Selenium WebDriver instance.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.
    '''
    logging.info(f"Setting date range: {start_date} to {end_date}")
    start_year, start_month, start_day = start_date.split('-')
    end_year, end_month, end_day = end_date.split('-')
    
    time.sleep(4)

    # Select "Custom" date range
    select = Select(driver.find_element(By.ID, "dr"))
    select.select_by_visible_text("Enter date range...")
    logging.info("Selected 'Enter date range...' option")
    time.sleep(1.5)

    # Fill in "From" date fields
    driver.find_element(By.ID, 'frd').clear()
    driver.find_element(By.ID, 'frd').send_keys(start_day)

    driver.find_element(By.ID, 'frm').clear()
    driver.find_element(By.ID, 'frm').send_keys(start_month)

    driver.find_element(By.ID, 'fry').clear()
    driver.find_element(By.ID, 'fry').send_keys(start_year)

    # Fill in "To" date fields
    driver.find_element(By.ID, 'tod').clear()
    driver.find_element(By.ID, 'tod').send_keys(end_day)

    driver.find_element(By.ID, 'tom').clear()
    driver.find_element(By.ID, 'tom').send_keys(end_month)

    driver.find_element(By.ID, 'toy').clear()
    driver.find_element(By.ID, 'toy').send_keys(end_year)
    logging.info("Date range fields updated")

# Define function to change language to english only
def change_language(driver):
    '''
    Change the language in the Factiva search interface.
    
    Args:
        driver (webdriver): Selenium WebDriver instance.
    '''
    logging.info("Setting language to English")
    time.sleep(4)
    driver.find_element(By.ID, "laTab").click()
    time.sleep(4)
    english_link = driver.find_element(By.XPATH, "//a[text()='English' and @class='mnuItm']")
    driver.execute_script("arguments[0].click();", english_link)
    logging.info("Language set to English")

# Define function to change region
def change_region(driver):
    #### Change region ####
    logging.info("Setting region to United Kingdom")
    time.sleep(4)
    driver.find_element(By.XPATH, "//a[text()='Region' and contains(@class, 'fesTabLinkFix')]").click()
    time.sleep(4)

    # 2. Type "United Kingdom" in the search box
    region_input = driver.find_element(By.ID, "reTxt")
    region_input.clear()
    region_input.send_keys("United Kingdom")
    time.sleep(4)  # wait for dropdown to appear

    # 3. Click button
    driver.find_element(By.ID, "reLkp").click()
    time.sleep(4)

    # 4 find uk in list and click it
    driver.find_element(By.XPATH, "//a[text()='United Kingdom' and contains(@class, 'mnuItm')]").click()
    time.sleep(4)
    logging.info("Region set to United Kingdom")

# Internal function to add a subject
def add_subject(subject_name):
    # Ensure the Subject tab is open before calling this
    subject_input = driver.find_element(By.ID, "nsTxt")
    subject_input.clear()
    subject_input.send_keys(subject_name)
    time.sleep(4)

    # Try clicking suggestion (strong) first
    try:
        driver.find_element(By.XPATH, f"//strong[text()='{subject_name}']/ancestor::td").click()
        logging.info(f"Selected via suggestion: {subject_name}")
    except:
        # Fallback: click direct <a> tag
        driver.find_element(By.XPATH, f"//a[text()='{subject_name}' and contains(@class, 'mnuItm')]").click()
        logging.info(f"Selected via <a>: {subject_name}")
    time.sleep(4)
 
# Define function to change subject
def change_subject(driver):
    logging.info("Adding subjects...")
    subjects_to_add = [
    "Commodity/Financial Market News",
    "Corporate/Industrial News",
    "Economic News"
    ]
    
    # Open the Subject tab once
    driver.find_element(By.XPATH, "//a[text()='Subject' and contains(@class, 'fesTabLinkFix')]").click()
    time.sleep(4)

    # Update
    for s in subjects_to_add:
        add_subject(s)
        
    # Close the Subject tab by clicking it again
    driver.find_element(By.XPATH, "//a[text()='Subject' and contains(@class, 'fesTabLinkFix')]").click()
    time.sleep(4)
    logging.info("Subjects added")

# Define function other minor settings
def other_settings(driver):
    logging.info("Setting other search parameters")
    time.sleep(2)
    # Add key search terms in search box at the top
    driver.execute_script("""
        let editor = ace.edit(document.getElementsByClassName('ace_editor')[0]);
        editor.setValue('rst=tukn');
    """)
    
    # Remove some of the "more options"
    driver.find_element(By.XPATH, "//a[contains(text(), 'More Options')]").click()
    time.sleep(4)

    # Check the box if not already checked
    checkbox = driver.find_element(By.ID, "isteo_bool")
    if not checkbox.is_selected():
        checkbox.click()
        time.sleep(4)
    logging.info("Other search parameters set")
        
# Function to define industry
def change_industry(driver, industry):
    logging.info(f"Changing industry to {industry}")
    #### Industry ####
    driver.find_element(By.XPATH, "//a[text()='Industry' and contains(@class, 'fesTabLinkFix')]").click()
    time.sleep(4)

    # 2. Type the industry name in the input box
    industry_input = driver.find_element(By.ID, "inTxt")
    industry_input.clear()
    industry_input.send_keys(industry)
    time.sleep(4)

    # 3. Click the blue play/search icon
    driver.find_element(By.ID, "inLkp").click()
    time.sleep(4)

    # 4. Click the search result matching the industry name
    driver.find_element(By.XPATH, f"//a[text()='{industry}' and contains(@class, 'mnuItm')]").click()
    time.sleep(4)
    logging.info(f"Industry set to {industry}")

# Function to define industry ad remove old when it changes
def change_industry_remove_old(driver, industry,last_industry):
    logging.info(f"Changing industry to {industry}")
    
    time.sleep(2)
    #### Industry ####
    wait_and_get_element(driver, By.XPATH, "//a[text()='Industry' and contains(@class, 'fesTabLinkFix')]").click()
    time.sleep(4)

    # 2. Type the industry name in the input box
    industry_input = wait_and_get_element(driver, By.ID, "inTxt")
    industry_input.clear()
    industry_input.send_keys(industry)
    time.sleep(4)

    # 3. Click the blue play/search icon
    wait_and_get_element(driver, By.ID, "inLkp").click()
    time.sleep(4)

    # 4. Click the search result matching the industry name
    wait_and_get_element(driver, By.XPATH, f"//a[text()='{industry}' and contains(@class, 'mnuItm')]").click()
    time.sleep(4)
    
    logging.info(f"Removing old industry {last_industry}")
    old_label = wait_and_get_element(driver, By.XPATH, f"//span[text()='{last_industry}' and contains(@class, 'filterText')]")
    old_label.click()
    time.sleep(1)

    # Click the adjacent 'Remove' button that appears in dropdown
    remove_button = wait_and_get_element(driver, By.XPATH, "//span[text()='Remove']")
    remove_button.click()
    time.sleep(2)
    logging.info(f"Old industry {last_industry} removed")

# Define function to click search button
def click_search_button(driver):
    '''
    Click the search button in the Factiva search interface.
    
    Args:
        driver (webdriver): Selenium WebDriver instance.
    '''
    logging.info("Clicking search button")
    # Click the search button at the bottom
    time.sleep(4)
    driver.find_element(By.XPATH, '//*[@id="btnSearchBottom"]').click()
    time.sleep(7)
    logging.info("Search button clicked")

# Function to get results and export
def get_results_and_export(driver,industry,base_folder,start_date, end_date):
    logging.info("Extracting and saving results")
    # Extract rows from the summary table
    summary_data = driver.find_elements(By.XPATH, "//tbody/tr[td[@class='label']]")

    summary_dict = {}
    for row in summary_data:
        try:
            key = row.find_element(By.XPATH, "./td[1]").text.strip()
            value = row.find_element(By.XPATH, "./td[2]").text.strip()
            summary_dict[key] = value
        except:
            continue
        
    try:
        dedup_value = driver.find_element(By.ID, "dedupSummary").text
        summary_dict["Deduplication Summary"] = dedup_value
    except:
        summary_dict["Deduplication Summary"] = ""
    
    # Ensure industry-specific folder exists
    industry_folder = os.path.join(base_folder, industry.replace("/", "_"))
    os.makedirs(industry_folder, exist_ok=True)

    # Construct filename and path
    filename = f"{start_date}_to_{end_date}.csv"
    csv_path = os.path.join(industry_folder, filename)

    # Write CSV
    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_dict.keys())
        writer.writeheader()
        writer.writerow(summary_dict)
    
    time.sleep(4)
    logging.info(f"Results saved to {csv_path}")

# Function to click modify search button
def click_modify_search_button(driver):
    '''
    Click the "Modify Search" button in the Factiva search interface.
    
    Args:
        driver (webdriver): Selenium WebDriver instance.
    '''
    logging.info("Clicking modify search button")
    time.sleep(4)
    driver.find_element(By.XPATH, '//*[@id="btnModifySearch"]').click()
    time.sleep(4)
    logging.info("Modify search button clicked")
        
# Main function with all tasks
def run_scraper_tasks(industry, 
                      start_date, 
                      end_date, 
                      last_industry,
                      first_iteration,
                      DATA_SAVE_FOLDER):
    '''
    Main function
    Run the scraper tasks for each industry and date range.
    '''
    logging.info(f"Starting scraper task for {industry} from {start_date} to {end_date}")
    
    # Initialize the WebDriver
    driver = init_driver()
    
    if first_iteration:
        logging.info("First iteration: performing full setup")
        # Change the date range
        change_date_range(driver,start_date,end_date)
        
        # Change language
        change_language(driver)
        
        # Change region
        change_region(driver)
        
        # Change subject
        change_subject(driver)
        
        # Other settings
        other_settings(driver)
        
        # Change industry
        change_industry(driver, industry)
        
        # Click search button
        click_search_button(driver)
        
        # Save results and export
        get_results_and_export(driver, industry, DATA_SAVE_FOLDER, start_date, end_date)
        
        # Click modify search button
        click_modify_search_button(driver)
        logging.info("First iteration setup complete")
        
    else:
        logging.info("Subsequent iteration: updating parameters")
        # If not the first iteration, just change the date
        change_date_range(driver, start_date, end_date)
        
        # Change industry if it has changed
        if industry != last_industry:
            logging.info(f"Changing industry from {last_industry} to {industry}")
            change_industry_remove_old(driver, industry,last_industry)
        
        # Click search button
        click_search_button(driver)
        
        # Save results and export
        get_results_and_export(driver, industry, DATA_SAVE_FOLDER, start_date, end_date)
        
        # Click modify search button
        click_modify_search_button(driver)
        logging.info("Subsequent iteration update complete")
    
    logging.info(f"Completed task for {industry} from {start_date} to {end_date}")