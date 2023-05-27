import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from random import randint
from time import sleep
import pickle
import re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains


if __name__ == '__main__':
    with open('list.txt', 'r') as file:
        top_journals = file.readlines()

    chrome_driver_path = 'chromedriver.exe'

    # Configure proxy settings. If you need...
    proxy_address = '127.0.0.1:7890'
    webdriver.DesiredCapabilities.CHROME['proxy'] = {
        "httpProxy": proxy_address,
        "ftpProxy": proxy_address,
        "sslProxy": proxy_address,
        "proxyType": "MANUAL",
    }

    chrome_options = Options()
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")

    # Launch WebDriver with proxy settings
    driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)
    actions = ActionChains(driver)


    def build_url(journal_name, start_seq):
        journal_split = journal_name.strip().split(' ')
        url = "https://scholar.google.com/scholar?start=" + str(start_seq) + "&q=source:" + journal_split[0].strip()
        if len(journal_split) >= 1:
            for split in journal_split[1:]:
                url += '+source:' + split.strip()

        # exclude citation
        url += "&as_vis=1"
        return url

    def build_keys(journal_name):
        journal_split = journal_name.strip().split(' ')
        key_str = ''
        for split in journal_split:
            key_str += 'source:' + split + " "

        return key_str

    # high frequency random mouse walk.
    def random_mouse_walk(actions):
        for i in range(10):
            actions.move_by_offset(randint(-20, 20), randint(-20, 20))
            sleep(random.uniform(0, 0.1))

    def scroll_down(driver):
        driver.execute_script("window.scrollBy(0, {});".format(randint(0, 1000)))

    def scroll_up(driver):
        driver.execute_script("window.scrollBy(0, {});".format(randint(-1000, 0)))

    def random_user_action(driver, actions):
        for i in range(10):
            roll = random.uniform(0, 1)
            if roll > 0.5:
                random_mouse_walk(actions)
            else:
                if roll > 0.75:
                    scroll_up(driver)
                else:
                    scroll_down(driver)

    def move_to_element(element, driver, actions):
        # Mock human interactive move to the element
        random_mouse_walk(actions)
        actions.move_to_element(element)


    paper_store = []
    file_idx = 0
    total_cnt = 0

    start_year = 1990
    end_year = 2023

    for journal in top_journals[:]:
        cur_year = start_year

        while cur_year <= end_year:
            driver.get("https://scholar.google.com")
            sleep(5)
            search_box = driver.find_element(By.NAME, "q")

            # throw in some random move!
            move_to_element(search_box, driver, actions)
            search_box.send_keys(build_keys(journal))
            search_box.send_keys(Keys.RETURN)
            sleep(5)
            random_user_action(driver, actions)

            # exclude citation:
            sidebar = driver.find_element(By.ID, "gs_bdy_sb")
            exclude_citation = sidebar.find_elements(By.CSS_SELECTOR, ".gs_lbl")[2]
            move_to_element(exclude_citation, driver, actions)
            exclude_citation.click()
            sleep(5)


            # advance search!
            custom_range = driver.find_element(By.ID, "gs_res_sb_yyc")
            move_to_element(custom_range, driver, actions)
            custom_range.click()
            sleep(random.uniform(0.1, 0.5))
            sidebar = driver.find_element(By.ID, "gs_bdy_sb")
            input_1 = sidebar.find_element(By.NAME, "as_ylo")
            move_to_element(input_1, driver, actions)
            input_1.send_keys(str(cur_year))
            input_2 = sidebar.find_element(By.NAME, "as_yhi")
            move_to_element(input_2, driver, actions)
            input_2.send_keys(str(cur_year))
            search_btn = sidebar.find_element(By.CLASS_NAME, "gs_btn_lsb")
            move_to_element(search_btn, driver, actions)
            search_btn.click()
            sleep(5)

            while True:
                papers = driver.find_elements(By.CSS_SELECTOR, ".gs_r.gs_or.gs_scl")
                for paper in papers:
                    title = paper.find_element(By.CLASS_NAME, "gs_rt")
                    title = title.text

                    # get citation from third child of "gs_fl"
                    try:
                        citation = paper.find_element(By.XPATH, '//div[@class="gs_fl"]')
                        citation = citation.find_elements(By.XPATH, './*')
                        match = re.match("\s*[^0-9]*\s*(\d*)", citation[2].text)
                        citation = eval(match.group(1))

                    except:
                        citation = 0

                    # get date
                    date = paper.find_element(By.CLASS_NAME, "gs_a")
                    match = re.match("[^0-9]*(\d*)[^0-9]*", date.text)
                    date = eval(match.group(1))

                    # get url
                    try:
                        url = paper.find_element(By.CLASS_NAME, "gs_or_ggsm")
                        url = url.find_elements(By.XPATH, './*')
                        url = url[0].get_attribute("href")
                    except:
                        url = ''

                    paper_store.append({
                        'journal': journal,
                        'title': title,
                        'citation': citation,
                        'date': date,
                        'url': url,
                    })
                    total_cnt += 1



                    if len(paper_store) >= 100:
                        print("Scraped " + str(total_cnt) + " papers.")
                        with open(str(file_idx) + '.pickle', 'wb') as file:

                            pickle.dump(paper_store, file)

                        paper_store = []
                        file_idx += 1

                        sleep(randint(10, 20))

                # GOTO next. if no next is found. complete!
                for i in range(3):
                    scroll_down(driver)
                next = driver.find_element(By.ID, "gs_n")
                next = next.find_element(By.CSS_SELECTOR, '[align="left"]')
                son = next.find_element(By.XPATH, './*')
                if son.get_attribute("href"):
                    move_to_element(next, driver, actions)
                    next.click()
                    sleep(randint(5, 15))
                else:
                    # end here!
                    print("Year " + str(cur_year) + " of " + journal + "is completed.")
                    break

            cur_year += 1