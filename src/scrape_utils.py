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
import shutil

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
    
    wait = WebDriverWait(driver, 1)

    # ---- Step 1: Click the Date Dropdown ----
    # Click the "Date" dropdown itself
    date_dropdown = wait.until(EC.element_to_be_clickable((By.ID, "dr")))
    date_dropdown.click()

    try:
        enter_range_option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//*[text()[contains(., 'Enter date range')]]"))
        )
        enter_range_option.click()
    except:
        print("Retrying dropdown click and selection")
        date_dropdown.click()
        time.sleep(1)
        enter_range_option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//*[text()[contains(., 'Enter date range')]]"))
        )
        enter_range_option.click()

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
    time.sleep(4)
    driver.find_element(By.ID, "laTab").click()
    time.sleep(4)
    english_link = driver.find_element(By.XPATH, "//a[text()='English' and @class='mnuItm']")
    driver.execute_script("arguments[0].click();", english_link)
    logging.info("Language set to English")

# Define function to change region
def change_region(driver):
    #### Change region ####
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
    time.sleep(2)
    # Add key search terms in search box at the top
    driver.execute_script("""
        let editor = ace.edit(document.getElementsByClassName('ace_editor')[0]);
        editor.setValue('rst=topuk');
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
    
# Define function other minor settings - except text
def other_settings_notext(driver):
    time.sleep(2)
    
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
    # Click the search button at the bottom
    time.sleep(4)
    driver.find_element(By.XPATH, '//*[@id="btnSearchBottom"]').click()
    time.sleep(7)
    logging.info("Search button clicked")

# Function to get results and export
def get_results_and_export(driver,industry,subfocus,base_folder,start_date, end_date):
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
        
    # Check if there are any results
    results_found = summary_dict.get("Results Found", "0")
    try:
        # Remove commas and convert to int
        results_count = int(results_found.replace(",", ""))
    except:
        results_count = 0
    
    logging.info(f"Results found: {results_count}")
    
    # if results_count == 0:
    #     logging.info("No results found - skipping file save and chart downloads")
    #     return 0  # Return 0 to indicate no results
    
    # Ensure industry-specific folder exists
    industry_folder = os.path.join(base_folder, industry.replace("/", "_"))
    os.makedirs(industry_folder, exist_ok=True)
    
    if subfocus:
        # Create subfocus folder
        subfocus_folder = os.path.join(industry_folder, subfocus.replace("/", "_"))
        os.makedirs(subfocus_folder, exist_ok=True)
        target_folder = subfocus_folder
    else:
        # No subfocus - create "no_subfocus" folder
        no_subfocus_folder = os.path.join(industry_folder, "no_subfocus")
        target_folder = no_subfocus_folder
        
    os.makedirs(target_folder, exist_ok=True)
    
    # Construct filename and path
    filename = f"{start_date}_to_{end_date}.csv"
    csv_path = os.path.join(target_folder, filename)

    # Write CSV
    with open(csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_dict.keys())
        writer.writeheader()
        writer.writerow(summary_dict)
    
    time.sleep(4)
    logging.info(f"Results saved to {csv_path}")
    if results_count == 0:
        logging.info("No results found - CSV saved but skipping chart downloads")
    else:
        logging.info(f"Found {results_count} results - CSV saved, proceeding with charts")
        
    return results_count 

# Function to click modify search button
def click_modify_search_button(driver):
    '''
    Click the "Modify Search" button in the Factiva search interface.
    
    Args:
        driver (webdriver): Selenium WebDriver instance.
    '''
    time.sleep(4)
    driver.find_element(By.XPATH, '//*[@id="btnModifySearch"]').click()
    time.sleep(4)
    logging.info("Modify search button clicked")
    
def safe_click(driver, xpath, retries=2, wait_time=5):
    for attempt in range(retries):
        try:
            btn = WebDriverWait(driver, wait_time).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            btn.click()
            return
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(2)
            
# def safe_close_overlay(driver):
#     try:
#         WebDriverWait(driver, 3).until(
#             EC.element_to_be_clickable((By.XPATH, "/html/body/div[14]/div/div[1]/div[2]"))
#         ).click()
#     except Exception as e:
#         print("[WARN] Failed to close overlay. Continuing anyway.")
        
def safe_close_overlay(driver):
    primary_xpath = "//*[@id='relInfoPopupBalloon']/div[1]/div[2]"
    try:
        close_btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, primary_xpath))
        )
        close_btn.click()
        return
    except:
        logging.warning("Primary close button xpath failed, trying fallback divs")

    for i in range(13, 20):
        try:
            xpath = f"/html/body/div[{i}]/div/div[1]/div[2]"
            close_btn = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            close_btn.click()
            logging.info(f"Overlay closed with fallback div[{i}]")
            return
        except:
            continue

    logging.warning("[WARN] Could not close overlay window after multiple strategies.")

def wait_for_file(path, timeout=10):
    for _ in range(timeout * 2):  # check every 0.5s
        if os.path.exists(path):
            return
        time.sleep(0.5)
    raise FileNotFoundError(f"Timed out waiting for {path}")
        
def export_csv(driver, export_xpath, download_name, dest_folder, prefix, start_date, end_date):    
    
    driver.switch_to.default_content()
    safe_click(driver, export_xpath)
    
    WebDriverWait(driver, 5).until(
        EC.frame_to_be_available_and_switch_to_it((By.NAME, "exportChartFrame"))
    )
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//span[text()='Download .CSV']"))
    ).click()
    
    driver.switch_to.default_content()
    safe_close_overlay(driver)
    
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    full_path = os.path.join(downloads_folder, f"{download_name}.csv")
    wait_for_file(full_path)

    # Format new filename and move
    start = start_date.replace('-', '')
    end = end_date.replace('-', '')
    new_name = f"{prefix}_{start}_{end}.csv"

    os.makedirs(dest_folder, exist_ok=True)
    shutil.move(full_path, os.path.join(dest_folder, new_name))

def get_sources_industry_subjects_folders(base_folder,subfocus,start_date,end_date,driver,industry):
    industry_folder = os.path.join(base_folder, industry.replace("/", "_"))
    
    if subfocus:
        # Create subfocus folder structure
        subfocus_folder = os.path.join(industry_folder, subfocus.replace("/", "_"))
        sources_folder = os.path.join(subfocus_folder, "sources")
        subjects_folder = os.path.join(subfocus_folder, "subjects")
        industries_folder = os.path.join(subfocus_folder, "industries")
    else:
        # No subfocus - use industry folder directly
        no_subfocus_folder = os.path.join(industry_folder, "no_subfocus")
        sources_folder = os.path.join(no_subfocus_folder, "sources")
        subjects_folder = os.path.join(no_subfocus_folder, "subjects")
        industries_folder = os.path.join(no_subfocus_folder, "industries")

    EXPORT_XPATHS = {
        "Source": "/html/body/form[2]/div[2]/div[2]/div[5]/div[2]/div[1]/div/div[3]/div/div[1]/span/a/span",
        "Subject": "/html/body/form[2]/div[2]/div[2]/div[5]/div[2]/div[1]/div/div[4]/div/div[1]/span/a/span",
        "Industry": "/html/body/form[2]/div[2]/div[2]/div[5]/div[2]/div[1]/div/div[5]/div/div[1]/span/a/span",
    }

    export_csv(driver, EXPORT_XPATHS["Source"], "Source", sources_folder, "sources", start_date, end_date)
    export_csv(driver, EXPORT_XPATHS["Subject"], "Subject", subjects_folder, "subjects", start_date, end_date)
    
    # Only download industries if no subfocus is specified
    if not subfocus:
        export_csv(driver, EXPORT_XPATHS["Industry"], "Industry", industries_folder, "industries", start_date, end_date)
    else:
        logging.info(f"Subfocus '{subfocus}' specified - skipping industry chart download")

def set_search_text(driver, text):
    """
    Set text in the Factiva free text search box (ACE editor).
    
    Args:
        driver: Selenium WebDriver instance
        text (str): Text to set in the search box
    """
    try:
        driver.execute_script(f"""
            let editor = ace.edit(document.getElementsByClassName('ace_editor')[0]);
            editor.setValue('{text}');
        """)
        logging.info(f"Set search text to: {text}")
        time.sleep(1)
        return True
    except Exception as e:
        logging.error(f"Failed to set search text: {e}")
        return False

def add_search_text(driver, additional_text):
    """
    Add text to existing content in the Factiva free text search box.
    
    Args:
        driver: Selenium WebDriver instance
        additional_text (str): Text to add to existing search
    """
    try:
        driver.execute_script(f"""
            let editor = ace.edit(document.getElementsByClassName('ace_editor')[0]);
            let currentText = editor.getValue();
            let newText = currentText + ' {additional_text}';
            editor.setValue(newText);
        """)
        logging.info(f"Added to search text: {additional_text}")
        time.sleep(1)
        return True
    except Exception as e:
        logging.error(f"Failed to add search text: {e}")
        return False

def get_search_text(driver):
    """
    Get current text from the Factiva free text search box.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        str: Current search text
    """
    try:
        current_text = driver.execute_script("""
            let editor = ace.edit(document.getElementsByClassName('ace_editor')[0]);
            return editor.getValue();
        """)
        logging.info(f"Current search text: {current_text}")
        return current_text
    except Exception as e:
        logging.error(f"Failed to get search text: {e}")
        return ""

def clear_search_text(driver):
    """
    Clear all text from the Factiva free text search box.
    
    Args:
        driver: Selenium WebDriver instance
    """
    try:
        driver.execute_script("""
            let editor = ace.edit(document.getElementsByClassName('ace_editor')[0]);
            editor.setValue('');
        """)
        logging.info("Cleared search text")
        time.sleep(1)
        return True
    except Exception as e:
        logging.error(f"Failed to clear search text: {e}")
        return False

def replace_search_text(driver, old_text, new_text):
    """
    Replace specific text in the search box.
    
    Args:
        driver: Selenium WebDriver instance
        old_text (str): Text to replace
        new_text (str): Replacement text
    """
    try:
        driver.execute_script(f"""
            let editor = ace.edit(document.getElementsByClassName('ace_editor')[0]);
            let currentText = editor.getValue();
            let newText = currentText.replace('{old_text}', '{new_text}');
            editor.setValue(newText);
        """)
        logging.info(f"Replaced '{old_text}' with '{new_text}'")
        time.sleep(1)
        return True
    except Exception as e:
        logging.error(f"Failed to replace search text: {e}")
        return False


def set_industry_search_text(driver, industry):
    
    import re
    # Define industries code mapping
    industries_search_codes = {
        "All":"",
        "Agriculture":"i0",
        "Automotive":"iaut",
        "Basic Materials/Resources":"ibasicm",
        "Business/Consumer Services":"ibcs",
        "Consumer Goods":"incp",
        "Energy":"i1",
        "Financial Services":"ifinal",
        "Healthcare/Life Sciences":"i951",
        "Industrial Goods":"iindstrls",
        "Leisure/Arts/Hospitality":"ilea",
        "Media/Entertainment":"imed",
        "Real Estate/Construction":"icre",
        "Retail/Wholesale":"i64",
        "Technology":"itech",
        "Telecommunication Services":"i7902",
        "Transportation/Logistics":"itsp",
        "Utilities":"iutil"
    }
    
    # Get current search text
    current_search = get_search_text(driver)
    
    # Remove any existing industry codes (in=i### pattern)
    import re
    cleaned_search = re.sub(r'\s*AND\s*in=i\w+', '', current_search)
    cleaned_search = re.sub(r'in=i\w+\s*AND\s*', '', cleaned_search)
    cleaned_search = re.sub(r'in=i\w+', '', cleaned_search)
    cleaned_search = cleaned_search.strip()
    
    # Add new industry code if not "All"
    if industry != "All" and industry in industries_search_codes:
        industry_code = industries_search_codes[industry]
        if industry_code:
            new_search = f"{cleaned_search} AND in={industry_code}"
        else:
            new_search = cleaned_search
    else:
        new_search = cleaned_search
        
     # Set the new search text
    set_search_text(driver, new_search.strip())
    logging.info(f"Set industry filter for: {industry} ({industries_search_codes.get(industry, 'No code')})")
    return True

def set_subfocus_search(driver, subfocus):
    """
    Set subfocus filter by replacing existing ns conditions.
    
    Args:
        driver: Selenium WebDriver instance
        subfocus (str): Subfocus name from subfocuses_codes mapping
    """
    import re
    
    # Define subfocus code mapping
    subfocuses_codes = {
        "Tariffs": "gtrade",  # Trade barriers/restrictions, under economic news (ecat)
        "Supply Chain": "cscm"  # Under corporate/industrial news (ccat)
    }
    
    # Get current search text
    current_search = get_search_text(driver)
    
    # Remove any existing ns conditions
    # Remove patterns like: AND (ns=xxx OR ns=yyy OR ns=zzz)
    cleaned_search = re.sub(r'\s*AND\s*\([^)]*ns=[^)]*\)', '', current_search)
    # Remove patterns like: AND ns=xxx
    cleaned_search = re.sub(r'\s*AND\s*ns=\w+', '', cleaned_search)
    # Remove any leftover parentheses patterns
    cleaned_search = re.sub(r'\s*AND\s*\([^)]*\)', '', cleaned_search)
    # Clean up any multiple spaces
    cleaned_search = re.sub(r'\s+', ' ', cleaned_search)
    cleaned_search = cleaned_search.strip()
    
    # Add new subfocus code if specified
    if subfocus and subfocus in subfocuses_codes:
        subfocus_code = subfocuses_codes[subfocus]
        new_search = f"{cleaned_search} AND ns={subfocus_code}"
        logging.info(f"Set subfocus filter for: {subfocus} (ns={subfocus_code})")
    else:
        new_search = cleaned_search
        logging.info("Removed subfocus filter")
    
    # Set the new search text
    set_search_text(driver, new_search.strip())
    return True

def remove_subfocus_search(driver):
    """
    Remove any existing subfocus (ns) conditions from search.
    """
    return set_subfocus_search(driver, None)


# Main function with all tasks
def run_scraper_tasks_with_clicking(industry,
                                    subfocus, 
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
        
        if industry == "All":
            
            logging.info("First iteration: performing full setup - no industry specified")
            
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
            
            # Click search button
            click_search_button(driver)
            
            # Save results and export
            get_results_and_export(driver, industry, subfocus,DATA_SAVE_FOLDER, start_date, end_date)
            
            # Get sources, industries, and subjects folders
            get_sources_industry_subjects_folders(DATA_SAVE_FOLDER,start_date,end_date,driver,industry)
            
            # Click modify search button
            click_modify_search_button(driver)
        
        else:
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
            get_results_and_export(driver, industry, subfocus, DATA_SAVE_FOLDER, start_date, end_date)
            
            # Get sources, industries, and subjects folders
            get_sources_industry_subjects_folders(DATA_SAVE_FOLDER,start_date,end_date,driver,industry)
            
            # Click modify search button
            click_modify_search_button(driver)
        
        logging.info("First iteration setup complete")
        
    else:
        logging.info("Next iteration: updating parameters")
        # If not the first iteration, just change the date
        change_date_range(driver, start_date, end_date)
        
        # Change industry if it has changed
        if industry != last_industry and last_industry != "All":
            logging.info(f"Changing industry from {last_industry} to {industry}")
            change_industry_remove_old(driver, industry,last_industry)
        
        if last_industry == "All":
            logging.info("Last industry was 'All', skipping language, region, and subject changes")
            # Change industry
            change_industry(driver, industry)
            
        # Click search button
        click_search_button(driver)
        
        # Save results and export
        get_results_and_export(driver, industry, subfocus,DATA_SAVE_FOLDER, start_date, end_date)
        
        # Get sources, industries, and subjects folders
        get_sources_industry_subjects_folders(DATA_SAVE_FOLDER,start_date,end_date,driver,industry)
        
        # Click modify search button
        click_modify_search_button(driver)
        logging.info("Next iteration update complete")
    
    logging.info(f"Completed task for {industry} from {start_date} to {end_date}")
    
# Main function with all tasks - using the search text
def run_scraper_tasks(industry, 
                      subfocus,
                      start_date, 
                      end_date, 
                      last_industry,
                      last_subfocus,
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
        
        # Set text for only top uk newspapers sources
        set_search_text(driver, "rst=topuk")
        
        # Change language to english only
        add_search_text(driver, " AND la=en")
        
        # Change region to United Kingdom
        add_search_text(driver, " AND re=UK")
        
        # Change subjects to broad categories OR set subfocus if specified
        if subfocus and subfocus.strip():  # Check if subfocus exists and is not empty
            logging.info(f"Using subfocus: {subfocus}")
            set_subfocus_search(driver, subfocus)
        else:
            logging.info("Using broad subject categories")
            add_search_text(driver, " AND (ns=ccat OR ns=ecat OR ns=mcat)")
        
        # Add industry search text
        set_industry_search_text(driver, industry)
        
        # Other settings
        other_settings_notext(driver)
        
        # Click search button
        click_search_button(driver)
        
        # Save results and export
        results_count = get_results_and_export(driver, industry, subfocus,DATA_SAVE_FOLDER, start_date, end_date)
        
        # Only download charts if there are results
        # Set minimum threshold for chart downloads
        MIN_RESULTS_FOR_CHARTS = 3 # change also below
        if results_count >= MIN_RESULTS_FOR_CHARTS:
            #logging.info(f"Found {results_count} results - downloading charts")
            # Get sources, industries, and subjects folders
            get_sources_industry_subjects_folders(DATA_SAVE_FOLDER, subfocus, start_date, end_date, driver, industry)
        # else:
        #     logging.info("No results found - skipping chart downloads")
        
        # Click modify search button
        click_modify_search_button(driver)
        
        logging.info("First iteration setup complete")
        
    else:
        logging.info("Next iteration: updating parameters")
        
        # If not the first iteration, just change the date
        change_date_range(driver, start_date, end_date)
        
        # Change industry if needed
        # Only change industry if it has changed
        if industry != last_industry:
            logging.info(f"Industry changed from {last_industry} to {industry}")
            set_industry_search_text(driver, industry)
        else:
            logging.info(f"Industry unchanged: {industry}")
            
         # Change subfocus if needed
        if subfocus != last_subfocus:
            logging.info(f"Subfocus changed from {last_subfocus} to {subfocus}")
            if subfocus and subfocus.strip():
                set_subfocus_search(driver, subfocus)
            else:
                # If subfocus is None/empty, revert to broad categories
                logging.info("Reverting to broad subject categories")
                # Remove existing ns conditions and add broad categories
                current_search = get_search_text(driver)
                import re
                cleaned_search = re.sub(r'\s*AND\s*\([^)]*ns=[^)]*\)', '', current_search)
                cleaned_search = re.sub(r'\s*AND\s*ns=\w+', '', current_search)
                set_search_text(driver, f"{cleaned_search.strip()} AND (ns=ccat OR ns=ecat OR ns=mcat)")
        else:
            logging.info(f"Subfocus unchanged: {subfocus}")
                
        # Click search button
        click_search_button(driver)
        
        # Save results and export
        results_count = get_results_and_export(driver, industry,subfocus, DATA_SAVE_FOLDER, start_date, end_date)
        
        # Only download charts if there are results
        # Set minimum threshold for chart downloads
        MIN_RESULTS_FOR_CHARTS = 3
        if results_count >= MIN_RESULTS_FOR_CHARTS:
            #logging.info(f"Found {results_count} results - downloading charts")
            # Get sources, industries, and subjects folders
            get_sources_industry_subjects_folders(DATA_SAVE_FOLDER, subfocus, start_date, end_date, driver, industry)
        # else:
        #     logging.info("No results found - skipping chart downloads")
        
        # Click modify search button
        click_modify_search_button(driver)
        logging.info("Next iteration update complete")
    
    logging.info(f"Completed task for {industry} from {start_date} to {end_date}")
        