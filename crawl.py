import argparse
import json
import os
import re
from string import punctuation

import pypandoc
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import \
    expected_conditions as EC  # available since 2.26.0
from selenium.webdriver.support.ui import WebDriverWait  # available since 2.4.0
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm

marking = "?/{}/?"  # just shouldnt look like html tags

LAST_ANNOTATION = ()


def generate_marking(keywords):
    return marking.format("".join(keywords.split(" ")))


def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. ' + directory)


def html2latex(text):
    output = pypandoc.convert(text, 'latex', format='html',
                              extra_args=['-f', 'html+tex_math_dollars'])
    return output


def append_to_inner_html(el, text):
    old_text_raw = el.get_attribute("innerHTML")
    old_text_plain_length = len(el.text)

    new_text = old_text_raw + text
    driver.execute_script(
        "arguments[0].innerHTML = {};".format(json.dumps(new_text)), el)
    return old_text_plain_length


def replace_markings_by_footnote(text, annotations):
    for keywords, explanation, plain_text_len in annotations:
        marking = generate_marking(keywords)
        marking_len = len(marking)

        start = text.find(marking)
        while start != -1:
            start = text.find(marking)
            end = start + marking_len

            text = text[:start - plain_text_len] + "\emph{" + text[
                                                              start - plain_text_len:start] + "}\\footnote{\\emph{" + keywords + "}: " + explanation + "} " + text[
                                                                                                                                                              end:]
            start = text.find(marking)

    return text


def get_annotation(el, driver):
    # simple .click() could potentially fail
    driver.execute_script("arguments[0].click();", el)

    try:
        annotation_el = driver.find_element_by_class_name("annotation")
            # WebDriverWait(driver, 10).until(
            # EC.presence_of_element_located((By.CLASS_NAME, "annotation")))
    except NoSuchElementException:
        print("ERROR: Couldnt find the annotation for this element, skipping..")
        return None


    keywords = annotation_el.find_elements_by_tag_name("i")[0].text.rstrip(
        punctuation)  # since the source is pretty random of whether there is a trailing dot or not in between tags...
    explanation = annotation_el.text[len(keywords) + 2:]

    # bring the page back into a sane state, since the same el_id might be reused
    # causing the annotation box to disappear instead. -> clean up
    driver.execute_script("arguments[0].click();", el)

    return keywords, explanation


def insert_annotations_into_text(aid, driver):
    el = driver.find_element_by_id(aid)
    ret = get_annotation(el, driver)

    if ret:
        plain_text_len = append_to_inner_html(el, generate_marking(ret[0]))

        return ret[0], ret[1], plain_text_len  # get_attribute("innerHTML"))#)
    else:
        return ret # None


def collect_all_annotations_of_paragraph(paragraph):
    annotation_links = paragraph.find_elements_by_class_name("annotBtn")
    return [link.get_attribute("id") for link in annotation_links]


def convert_paragraph_to_latex(paragraph):
    # get annotation links
    annotation_ids = collect_all_annotations_of_paragraph(paragraph)
    annotations = [insert_annotations_into_text(aid, driver) for aid in
                   annotation_ids]

    annotations = [annon for annon in annotations if annon]

    text = paragraph.text
    text = re.sub('\\[.*?\\]', '', text)
    # Insert slashes for latex

    text = replace_markings_by_footnote(text, annotations)
    text = text.replace("&", "\&")
    text = "\\\\\n".join(text.split("\n"))

    return text


def pad_verse(text):
    return "\\begin{verse}[\\versewidth]\n" + text + "\n\\end{verse}\n\n"


def crawl_book_content(driver):
    main_content = driver.find_element_by_id("content")
    paragraphs = main_content.find_elements_by_tag_name("p")

    book = ""
    for paragraph in tqdm(paragraphs[1:]):
        pg_text = convert_paragraph_to_latex(paragraph) + "\\\\!"

        book += pg_text

    # Find the first white space

    return convert_paragraph_to_latex(
        paragraphs[0]) + "\n\n\\newpage" + pad_verse(book)


LINKS2CRAWL = [
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_1/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_2/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_3/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_4/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_5/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_6/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_7/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_8/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_9/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_10/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_11/text.shtml",
    "https://www.dartmouth.edu/~milton/reading_room/pl/book_12/text.shtml",
]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--driver', '-d', type=str, default='phantomjs',
                        help='Phantomjs, Chrome, Firefox supported',
                        required=False)
    args = parser.parse_args()

    # Obtain Driver
    print(" :: Obtaining Driver")
    # instantiate a chrome options object so you can set the size and headless preference
    options = Options()
    options.add_argument("--headless")

    # driver = webdriver.Chrome(chrome_options=options, executable_path='chromedriver')
    # FALLBACKS
    driver = webdriver.Firefox(firefox_options=options)  # make sure to change the import for options
    # driver = webdriver.Firefox() # for non-headless mode
    # driver = webdriver.PhantomJS() # headless alternative

    createFolder("./content")
    for idx, link in enumerate(LINKS2CRAWL, start=9):
        print("Crawling book:", idx)
        driver.get(link)
        content = crawl_book_content(driver)

        with open(os.path.join("content", "book{}.tex".format(idx)),
                  "w") as text_file:
            text_file.write(content)
