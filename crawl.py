import argparse
import json
import os
import re
from string import punctuation

import pypandoc
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
# from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options
from tqdm import tqdm

marking = "?/{}/?"  # just shouldnt look like html tags

LAST_ANNOTATION = ()

import re

def tex_escape(text):
    """
        FROM: https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
        https://creativecommons.org/licenses/by-sa/4.0/

        Change made in line15: unicode -> str in python3
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)


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
                                                              start - plain_text_len:start] + "}\\footnote{\\emph{" + keywords + "}: " + explanation + "}" + text[
                                                                                                                                                             end:]
            start = text.find(marking)

    return text


def get_annotation(el, driver):
    # simple .click() could potentially fail
    driver.execute_script("arguments[0].click();", el)

    try:
        annotation_el = driver.find_element_by_class_name("annotation")
        # inner_els = annotation_el.find_elements_by_xpath(".//*")
        # WebDriverWait(driver, 10).until(
        # EC.presence_of_element_located((By.CLASS_NAME, "annotation")))
    except NoSuchElementException:
        print("ERROR: Couldnt find the annotation for this element, skipping..")
        return None

    # preprocess the text:
    block_quotes = annotation_el.find_elements_by_tag_name("blockquote")
    [insert_block_quotes(bq) for bq in block_quotes]

    links = annotation_el.find_elements_by_tag_name("a")
    [insert_links(link) for link in links]


    keywords = annotation_el.find_elements_by_tag_name("i")[0].text.rstrip(
        punctuation)  # since the source is pretty random of whether there is a trailing dot or not in between tags...
    explanation = annotation_el.text[len(keywords) + 2:]

    # fix weird punctations in annotations
    explanation = explanation.rstrip(".").rstrip() + "."

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
        return ret  # None


def collect_all_annotations_of_paragraph(paragraph):
    annotation_links = paragraph.find_elements_by_class_name("annotBtn")
    return [link.get_attribute("id") for link in annotation_links]


def wrap_inner_html(el, front, back):
    old_text_raw = el.get_attribute("innerHTML")

    new_text = front + old_text_raw + back
    driver.execute_script(
        "arguments[0].innerHTML = {};".format(json.dumps(new_text)), el)


def insert_modern_english_overtext(paragraph):
    old_words = paragraph.find_elements_by_class_name("varspell")

    for word in old_words:
        new_spelling = word.get_attribute("title")

        # handle edges cases
        new_spelling = "{" + new_spelling + "}" if new_spelling == "height" else new_spelling
        front = '\\ruby{'
        back = "}{" + new_spelling + "}\\hphantom{ }"
        wrap_inner_html(word, front, back)


def insert_block_quotes(element):
    wrap_inner_html(element, "\\begin{quote}", "\\end{quote}")


def insert_links(element):
    # determine if internal or external by a simple check
    link = element.get_attribute("href")

    if link[:50] == "https://www.dartmouth.edu/~milton/reading_room/pl/":
        # internal link
        # get line number, if present
        pass

        # splt = link[50:].split("line#")
        # print(splt)
        # book_number = int(splt[0].split("/text.shtml")[0].split("_")[1])
        # line_number = int(splt[1]) if len(splt) == 2 else None
        # print("IntLink:",book_number, line_number)
    else:
        # external link
        wrap_inner_html(element, "\href{" + tex_escape(link) + "}{", "}")

def convert_paragraph_to_latex(paragraph):
    # Find all words which have a modern english hover text and replace
    # print(" :: Insert new spellings into HTML")
    insert_modern_english_overtext(paragraph)

    # Should be done last when it comes to preprocessing the text
    # get annotation links
    annotation_ids = collect_all_annotations_of_paragraph(paragraph)
    annotations = [insert_annotations_into_text(aid, driver) for aid in
                   annotation_ids]

    annotations = [annon for annon in annotations if annon]

    # Convert HTML to regular tex
    text = paragraph.text

    # Get rid of any [*] line number markings
    text = re.sub('\\[.*?\\]', '', text)

    text = replace_markings_by_footnote(text, annotations)

    # Some minor encapsulation (manually...cant use tex_escape anymore!)
    text = text.replace("&", "\&")

    # Finally insert line breaks for latex
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
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_2/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_3/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_4/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_5/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_6/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_7/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_8/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_9/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_10/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_11/text.shtml",
    # "https://www.dartmouth.edu/~milton/reading_room/pl/book_12/text.shtml",
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
    driver = webdriver.Firefox(
        firefox_options=options)  # make sure to change the import for options
    # driver = webdriver.Firefox() # for non-headless mode
    # driver = webdriver.PhantomJS() # headless alternative

    createFolder("./content")
    for idx, link in enumerate(LINKS2CRAWL, start=1):
        print("Crawling book:", idx)
        driver.get(link)
        content = crawl_book_content(driver)

        with open(os.path.join("content", "book{}.tex".format(idx)),
                  "w") as text_file:
            text_file.write(content)
