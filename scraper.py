import os.path
import random
from random import randint
from time import sleep
import pickle
import re
from playwright.sync_api import sync_playwright
from recaptcha_challenger import new_audio_solver

if __name__ == '__main__':
    with open('list.txt', 'r') as file:
        top_journals = file.readlines()


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
    def random_mouse_walk(page):
        for i in range(10):
            page.mouse.move(randint(-20, 20), randint(-20, 20))
            sleep(random.uniform(0, 0.1))


    def scroll_down(page):
        page.evaluate("window.scrollBy(0, {});".format(randint(0, 1000)))


    def scroll_up(page):
        page.evaluate("window.scrollBy(0, {});".format(randint(-1000, 0)))


    def random_user_action(page):
        for i in range(10):
            roll = random.uniform(0, 1)
            if roll > 0.5:
                random_mouse_walk(page)
            else:
                if roll > 0.75:
                    scroll_up(page)
                else:
                    scroll_down(page)


    def move_to_element(element):
        # Mock human interactive move to the element
        # random_mouse_walk(page)
        random_user_action(page)
        element.scroll_into_view_if_needed()


    def check_for_bot(page):
        # Check if there is a human check in the page!
        html = page.content()
        match = re.search(r'recaptcha', html)
        if match:
            return True
        else:
            return False


    def fuck_reCAPTCHA(page):
        print("Hit bot check.")
        fuck_reCAPTCHA_core(page)
        sleep(5)
        while check_for_bot(page):  # solve failed.
            page.reload()  # reload the page for a new bot test.
            sleep(30)
            if check_for_bot(page):  # sometimes the test just go away when reloaded.
                fuck_reCAPTCHA_core(page)


    def fuck_reCAPTCHA_core(page):
        try:
            solver = new_audio_solver()
            if solver.utils.face_the_checkbox(page):
                solver.anti_recaptcha(page)
            sleep(30)
        except:
            # Your computer might be sending queries, try again later
            print("Google : Your computer might be sending queries, try again later")
            sleep(600)


    paper_store = []
    file_idx = 0
    while True:
        if os.path.exists(os.path.join('infos', str(file_idx) + '.pickle')):
            file_idx += 1
        else:
            break
    print("History db found, start from " + os.path.join('infos', str(file_idx) + '.pickle'))

    total_cnt = 0

    start_year = 1990
    end_year = 2023

    with open('log', 'r') as file:
        output = file.readlines()
        if len(output) == 2:
            check_journal = output[0]
            check_year = int(output[1])
            finished_journal = True
        else:
            finished_journal = False

    # Launch Playwright
    with sync_playwright() as playwright:
        # google is happy if ur not Incognito mode.
        browser = playwright.chromium.launch_persistent_context(
            user_data_dir=os.path.join(os.getcwd(), 'chrome_context'), headless=False)

        page = browser.new_page()


        for journal in top_journals[:]:
            cur_year = start_year

            if (finished_journal == True) and (journal.strip() != check_journal.strip()):
                continue

            while cur_year <= end_year:
                if (finished_journal == True) and cur_year < check_year:
                    cur_year += 1
                    continue
                elif (finished_journal == True) and cur_year == check_year:
                    finished_journal = False
                    cur_year += 1
                    continue

                page.goto("https://scholar.google.com")
                sleep(5)

                if check_for_bot(page):
                    fuck_reCAPTCHA(page)

                search_box = page.wait_for_selector('[name="q"]')
                move_to_element(search_box)
                search_box.fill(build_keys(journal))
                sleep(randint(0, 1))
                search_box.press('Enter')
                sleep(5)
                random_user_action(page)

                if check_for_bot(page):
                    fuck_reCAPTCHA(page)

                # exclude citation:
                sidebar = page.wait_for_selector('#gs_bdy_sb')
                exclude_citation = sidebar.query_selector_all('.gs_lbl')
                move_to_element(exclude_citation[2])
                exclude_citation[2].click()
                sleep(5)

                if check_for_bot(page):
                    fuck_reCAPTCHA(page)

                # advance search!
                custom_range = page.wait_for_selector('#gs_res_sb_yyc')
                move_to_element(custom_range)
                custom_range.click()
                sleep(random.uniform(0.1, 0.5))
                sidebar = page.wait_for_selector('#gs_bdy_sb')
                input_1 = sidebar.wait_for_selector('[name="as_ylo"]')
                move_to_element(input_1)
                input_1.fill(str(cur_year))
                input_2 = sidebar.wait_for_selector('[name="as_yhi"]')
                move_to_element(input_2)
                input_2.fill(str(cur_year))
                search_btn = sidebar.wait_for_selector('.gs_btn_lsb')
                move_to_element(search_btn)
                search_btn.click()
                sleep(5)

                if check_for_bot(page):
                    fuck_reCAPTCHA(page)

                while True:
                    sleep(5)
                    if check_for_bot(page):
                        fuck_reCAPTCHA(page)

                    papers = page.query_selector_all('.gs_r.gs_or.gs_scl')
                    for paper in papers:
                        title = paper.query_selector('.gs_rt')
                        title = title.text_content()
                        try:
                            url2 = paper.query_selector('.gs_rt')
                            url2 = url2.query_selector('a[href]')
                            url2 = url2.get_attribute("href")
                        except:
                            url2 = ''

                        # get citation from third child of "gs_fl"
                        try:
                            citation = paper.query_selector('.gs_ri')
                            citation = citation.query_selector('.gs_fl')
                            citation = citation.query_selector_all('xpath=./*')
                            match = re.match("\s*[^0-9]*\s*(\d*)", citation[2].text_content())
                            citation = eval(match.group(1))

                        except:
                            citation = 0

                        date = cur_year

                        # get url1
                        try:
                            url1 = paper.query_selector('.gs_or_ggsm')
                            url1 = url1.query_selector_all('xpath=./*')
                            url1 = url1[0].get_attribute("href")
                        except:
                            url1 = ''

                        paper_store.append({
                            'journal': journal,
                            'title': title,
                            'citation': citation,
                            'date': date,
                            'url1': url1,
                            'url2': url2,
                        })
                        total_cnt += 1

                        if len(paper_store) >= 100:
                            print("Scraped " + str(total_cnt) + " papers.")
                            with open(os.path.join('infos', str(file_idx) + '.pickle'), 'wb') as file:
                                pickle.dump(paper_store, file)

                            paper_store = []
                            file_idx += 1

                            sleep(randint(5, 15))

                    # GOTO next. if no next is found. complete!
                    for i in range(3):
                        scroll_down(page)

                    sleep(randint(10, 30))

                    try:
                        next = page.query_selector('#gs_n')
                        next = next.query_selector('[align="left"]')
                        son = next.query_selector('xpath=./*')
                        if son.get_attribute("href"):
                            move_to_element(next)
                            next.click()
                        else:
                            # end here!
                            print("Year " + str(cur_year) + " of " + journal + "is completed.")
                            with open("log", "w") as file:
                                file.writelines([journal, str(cur_year)])
                            # flush.
                            with open(os.path.join('infos', str(file_idx) + '.pickle'), 'wb') as file:
                                pickle.dump(paper_store, file)

                            paper_store = []
                            file_idx += 1
                            break
                    except:
                        print("Year " + str(cur_year) + " of " + journal + "is completed.")
                        with open("log", "w") as file:
                            file.writelines([journal, str(cur_year)])
                        # flush.
                        with open(os.path.join('infos', str(file_idx) + '.pickle'), 'wb') as file:
                            pickle.dump(paper_store, file)

                        paper_store = []
                        file_idx += 1
                        break

                cur_year += 1

        # flush.
        with open(os.path.join('infos', str(file_idx) + '.pickle'), 'wb') as file:
            pickle.dump(paper_store, file)

        paper_store = []
        file_idx += 1
