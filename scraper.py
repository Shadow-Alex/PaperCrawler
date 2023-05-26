from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import re


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

    # Launch WebDriver with proxy settings
    driver = webdriver.Chrome(executable_path=chrome_driver_path)

    def build_url(journal_name, start_seq):
        journal_split = journal_name.split(' ')
        url = "https://scholar.google.com/scholar?start=" + str(start_seq) + "&q=source:" + journal_split[0]
        if len(journal_split) >= 1:
            for split in journal_split[1:]:
                url += '+source:' + split

        return url

    for journal in top_journals:
        # advance search!
        url = build_url(journal, 0)
        driver.get(url)

        # try to find total result counts:
        elements = driver.find_elements(By.CLASS_NAME, "gs_ab_mdw")
        cnt_str = elements[1].text
        match = re.match(r'找到约 (.*) 条结果', cnt_str)
        cnt = int(match.group(1).replace(',', ''))

        # we have 10 results per page.
        elements = driver.find_elements(By.CLASS_NAME, "gs_rt")
        papers = [{} for i in range(len(elements))]
        for idx, elem in enumerate(elements):
            papers[idx]['title'] = elem.text

        elements = driver.find_elements(By.XPATH, '//div[@class="gs_fl"]')
        for idx, elem in enumerate(elements):
            child_elem = elem.find_elements(By.XPATH, './*')
            match = re.match("\s*[^0-9]*\s*(\d*)", child_elem[2].text)
            papers[idx]['cite'] = eval(match.group(1))

        sleep(10)

    driver.quit()