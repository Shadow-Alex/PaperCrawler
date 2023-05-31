import re
import hashlib
import logging
import os
import requests
import urllib3
import pickle
from time import sleep
import itertools
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
import time
from selenium.webdriver.common.by import By

# log config
logging.basicConfig()
logger = logging.getLogger('Sci-Hub')
logger.setLevel(logging.DEBUG)
urllib3.disable_warnings()

# constants
SCHOLARS_BASE_URL = 'https://scholar.google.com/scholar'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0'}


class SciHub(object):
    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers = HEADERS
        self.available_base_url_list = self._get_available_scihub_urls()
        self.available_backbone_url_list = self._get_available_scihub_backbone_urls()
        self.cycle_iter = itertools.cycle(self.available_base_url_list)
        self.cycle_bb = itertools.cycle(self.available_backbone_url_list)
        self.base_url = self.available_base_url_list[0] + '/'
        self.sess.proxies = {
            "http": 'http://127.0.0.1:7890',
            "https": 'https://127.0.0.1:7890', }

        # init a selenium driver :)
        chrome_driver_path = 'chromedriver.exe'
        proxy_address = '127.0.0.1:7890'
        webdriver.DesiredCapabilities.CHROME['proxy'] = {
            "httpProxy": proxy_address,
            "ftpProxy": proxy_address,
            "sslProxy": proxy_address,
            "proxyType": "MANUAL",
        }
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_experimental_option('prefs', {
            "download.default_directory": "E:\\Scholar crawler\\chrome_pdfs",
            # This is a bug in selenium, you need to specify absolute path.
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })

        self.driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

    def _get_available_scihub_urls(self):
        return ['https://sci-hub.ee', 'https://sci-hub.shop', 'https://sci-hub.se', 'https://sci-hub.st',
                'http://sci-hub.is', 'https://sci.hubg.org', 'https://sci.hubbza.co.za', 'https://sci-hub.ru',
                'https://sci-hub.hkvisa.net', 'https://sci-hub.mksa.top', 'http://sci-hub.ren', 'https://sci-hub.wf']

    def _get_available_scihub_backbone_urls(self):
        return ['https://sci-hub.se', 'https://sci-hub.st', 'https://sci-hub.ru', 'https://sci.hubg.org/']

    def _change_base_url(self):
        self.base_url = next(self.cycle_iter)
        # logger.info("I'm changing to {}".format(self.base_url))

    def _change_backbone_url(self):
        self.base_url = next(self.cycle_bb)
        # logger.info("I'm changing to {}".format(self.base_url))

    def download(self, identifier, destination='', path=None):
        # load balancing.
        data = self.fetch(identifier)

        return data

    def fetch(self, identifier):
        """
        Original -> Scihub -> Scihub backbone
        """
        try:
            # Try download !
            shutil.rmtree("chrome_pdfs")
            os.makedirs("chrome_pdfs")
            self.driver.get(identifier)
            direct_succ = False
            sleep_time = 0
            sleep_limit = 5
            sleep_max = 10
            while sleep_time < sleep_limit:
                sleep(1)
                sleep_time += 1

                if len(os.listdir('chrome_pdfs')) == 1:
                    filename = os.listdir('chrome_pdfs')[0]
                    _, f_ext = os.path.splitext(filename)
                    if f_ext == '.pdf':  # we might found .crdownload
                        old_filename = filename
                        filename = str(time.time()) + '_' + filename
                        shutil.move(os.path.join('chrome_pdfs', old_filename), os.path.join('pdfs', filename))
                        direct_succ = True
                        break
                    else:  # still downloading!
                        sleep_limit += 1
                        sleep_limit = min(sleep_max, sleep_limit)
            if direct_succ:
                return {
                    'direct': True,
                    'pdf': None,
                    'url': identifier,
                    'name': filename,
                }
        except:
            pass

        try:
            print("Falling back to scihub.")
            self._change_base_url()
            self.driver.get(self.base_url + '/' + identifier)
            btn = self.driver.find_element(By.XPATH,
                                           "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save') "
                                           "or contains(text(), '下载')]")
            btn.click()
            sci_succ = False
            sleep_time = 0
            sleep_limit = 5
            sleep_max = 10
            while sleep_time < sleep_limit:
                sleep(1)
                sleep_time += 1

                if len(os.listdir('chrome_pdfs')) == 1:
                    filename = os.listdir('chrome_pdfs')[0]
                    _, f_ext = os.path.splitext(filename)
                    if f_ext == '.pdf':  # we might found .crdownload
                        old_filename = filename
                        filename = str(time.time()) + '_' + filename
                        shutil.move(os.path.join('chrome_pdfs', old_filename), os.path.join('pdfs', filename))
                        sci_succ = True
                        break
                    else:  # still downloading!
                        sleep_limit += 1
                        sleep_limit = min(sleep_max, sleep_limit)

            if sci_succ:
                return {
                    'direct': True,
                    'pdf': None,
                    'url': identifier,
                    'name': filename,
                }
        except:
            pass

        try:
            print("Falling back to scihub backbone.")
            self._change_backbone_url()
            self.driver.get(self.base_url + '/' + identifier)
            btn = self.driver.find_element(By.XPATH,
                                           "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'save') "
                                           "or contains(text(), '下载')]")
            btn.click()
            sci_succ = False
            sleep_time = 0
            sleep_limit = 5
            sleep_max = 10
            while sleep_time < sleep_limit:
                sleep(1)
                sleep_time += 1

                if len(os.listdir('chrome_pdfs')) == 1:
                    filename = os.listdir('chrome_pdfs')[0]
                    _, f_ext = os.path.splitext(filename)
                    if f_ext == '.pdf':  # we might found .crdownload
                        old_filename = filename
                        filename = str(time.time()) + '_' + filename
                        shutil.move(os.path.join('chrome_pdfs', old_filename), os.path.join('pdfs', filename))
                        sci_succ = True
                        break
                    else:  # still downloading!
                        sleep_limit += 1
                        sleep_limit = min(sleep_max, sleep_limit)

            if sci_succ:
                return {
                    'direct': True,
                    'pdf': None,
                    'url': identifier,
                    'name': filename,
                }
        except:
            pass

    def _generate_name(self, res):
        """
        Generate unique filename for paper. Returns a name by calcuating 
        md5 hash of file contents, then appending the last 20 characters
        of the url which typically provides a good paper identifier.
        """
        name = res.url.split('/')[-1]
        name = re.sub('#view=(.+)', '', name)
        pdf_hash = hashlib.md5(res.content).hexdigest()
        return '%s-%s' % (pdf_hash, name[-20:])


class CaptchaNeedException(Exception):
    pass


if __name__ == '__main__':
    sh = SciHub()
    logger.setLevel(logging.DEBUG)

    file_idx = 0
    paper_idx = 0
    success_total_cnt = 0

    with open("download_log", 'r') as file:
        checkpoint = file.readlines()
        if len(checkpoint) != 0:
            file_idx = int(checkpoint[0])
            paper_idx = int(checkpoint[1]) + 1
            print("Checkpoint found, download from " + str(file_idx) + '.pickle ' + ' paper id : ' + str(paper_idx))

    while True:
        # find for *.pickle
        if os.path.exists(str(file_idx) + '.pickle'):
            success_cnt = 0

            print("Downloading papers in " + str(file_idx) + '.pickle...')
            with open(str(file_idx) + '.pickle', "rb") as file:
                papers_info = pickle.load(file)
            while paper_idx < len(papers_info):
                sleep(2)
                success = False
                url1 = papers_info[paper_idx]['url1']
                if url1 != '':
                    result = None
                    try:
                        result = sh.download(url1, destination='pdfs')
                    except Exception as e:
                        print(str(e))
                    if result is None:
                        logger.debug("Failed. continue...")
                    else:
                        success = True
                        papers_info[paper_idx]['filename'] = result['name']

                        with open(str(file_idx) + '.pickle', "wb") as file:
                            pickle.dump(papers_info, file)
                        with open("download_log", 'w') as file:
                            file.write(str(file_idx) + '\n')
                            file.write(str(paper_idx) + '\n')
                        success_cnt += 1
                        success_total_cnt += 1
                url2 = papers_info[paper_idx]['url2']
                if url2 != '' and not success:
                    result = None
                    try:
                        result = sh.download(url2, destination='pdfs')
                    except Exception as e:
                        logger.debug(str(e))
                    if result is None:
                        logger.debug("Failed. continue...")
                    else:
                        success = True
                        papers_info[paper_idx]['filename'] = result['name']

                        with open(str(file_idx) + '.pickle', "wb") as file:
                            pickle.dump(papers_info, file)
                        with open("download_log", 'w') as file:
                            file.write(str(file_idx) + '\n')
                            file.write(str(paper_idx) + '\n')
                        success_cnt += 1
                        success_total_cnt += 1
                paper_idx += 1
            paper_idx = 0
            file_idx += 1
            print(str(file_idx) + '.pickle is done. ' + ' Downloaded ' + str(success_cnt) + ' , ' + str(
                success_total_cnt) + ' total.')

        else:
            # seem unlikely lol..
            break
