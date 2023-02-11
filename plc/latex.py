import re
from string import punctuation
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from plc.consts import ANIMATION_TIME_S

from .html import (
    wrap_inner_html,
    append_to_inner_html,
    replace_inner_html,
    modify_inner_html,
)

INTERNAL_LINK_PREFIX = "https://www.dartmouth.edu/~milton/reading_room/pl/"

ESCAPE_MAPPING = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\^{}",
    "\\": r"\textbackslash{}",
    "<": r"\textless{}",
    ">": r"\textgreater{}",
}


def tex_escape(text, mapping):
    """
    FROM: https://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
    https://creativecommons.org/licenses/by-sa/4.0/

    Change made in line15: unicode -> str in python3
    :param text: a plain text message
    :return: the message escaped to appear correctly in LaTeX
    """

    regex = re.compile("|".join(re.escape(str(key)) for key in sorted(mapping.keys(), key=lambda item: -len(item))))
    return regex.sub(lambda match: mapping[match.group()], text)


def insert_link(driver, element):
    # determine if internal or external by a simple check
    link = element.get_attribute("href")

    if link:
        # Detect internal links
        if (link[:len(INTERNAL_LINK_PREFIX)] == INTERNAL_LINK_PREFIX or link[:3] == "../"):
            spl = link.split("#")
            if len(spl) == 2:
                book = spl[0].split("/")[-2]
                label = f"{book}_{spl[1]}"

                append_to_inner_html(driver, element, "\\ref{" + label + "}")
        else:
            # external link
            wrap_inner_html(driver, element, "\href{" + tex_escape(link, ESCAPE_MAPPING) + "}{", "}")
    else:
        raise NotImplementedError


STYLE_MAPPING = {
    "annotation_keyword": ("\\emph{", "}"),
    "quote": ("\\begin{quote}", "\\end{quote}"),
    "link": insert_link,
    "annotated": ("\\emph{", "}"),
    "footnote": ("\\footnote{", "}"),
}


def insert_modern_english_overtext(driver, paragraph):
    old_words = paragraph.find_elements(By.CSS_SELECTOR, "span[class='tooltip tooltipstered']")
    for word in old_words:
        try:
            modify_inner_html(driver, word, lambda x: x)
            new_spelling = word.get_attribute("title")

            # # handle edges cases
            # new_spelling = (
            #     "{{" + new_spelling + "}}" if new_spelling == "height" else new_spelling
            # )
            front = "\\ruby{{"
            back = "}}{{" + new_spelling + "}}\\hphantom{}"
            wrap_inner_html(driver, word, front, back)
        except StaleElementReferenceException:
            pass


def insert_line_labels(driver, content, label_prefix):
    """Lines are referenced with a special class.
    This inserts \labels{line:NUM} at the respective locations
    replacing existing content."""
    line_els = content.find_elements(By.CLASS_NAME, "line")
    for el in line_els:
        el_id = el.get_attribute("id")
        if el_id:
            # non-empty string
            replace_inner_html(driver, el, "\label{{{}_{}}}".format(label_prefix, el_id))
        else:
            # delete it, no label
            replace_inner_html(driver, el, "")


def insert_word_labels(driver, content, label_prefix):
    line_els = driver.find_elements(By.TAG_NAME, "a")
    for el in line_els:
        name = el.get_attribute("name")
        el_id = el.get_attribute("id")
        href = el.get_attribute("href")
        if name and not el_id and not href:
            # non-empty string
            replace_inner_html(driver, el, "\label{{{}_{}}}".format(label_prefix, name))
        else:
            # delete it, no label
            replace_inner_html(driver, el, "")


def get_annotation_el(driver, el):
    # simple .click() could potentially fail
    driver.execute_script("arguments[0].click();", el)

    try:
        annotation_el = WebDriverWait(driver, ANIMATION_TIME_S).until(
            EC.presence_of_element_located((By.CLASS_NAME, "annotation")))

        # annotation_el = driver.find_element(By.CLASS_NAME, "annotation")
    except NoSuchElementException:
        print("ERROR: Couldnt find the annotation for this element, skipping..")
        return None
    except TimeoutException:
        print("ERROR: Couldnt find the annotation for this element, skipping... [timeout]")
        print(el.text)
        return None

    return annotation_el


def style_element(driver, el, style_type):
    if style_type in STYLE_MAPPING:
        if callable(STYLE_MAPPING[style_type]):
            # special processing
            STYLE_MAPPING[style_type](driver, el)
        else:
            wrap_inner_html(driver, el, *STYLE_MAPPING[style_type])
    else:
        raise ValueError(f"Unknown style type `{style_type}`!")


def find_annotation_candidates(driver, content):
    return content.find_elements(By.CSS_SELECTOR, "a[class='annotBtn tooltipstered']")


def stylize_annotation(driver, outer_el):
    # (tag, style)
    for tag_type, style in [
        ("i", "annotation_keyword"),
        ("blockquote", "quote"),
        ("a", "link"),
    ]:
        els = outer_el.find_elements(By.TAG_NAME, tag_type)
        for el in els:
            style_element(driver, el, style)

    modify_inner_html(driver, outer_el, lambda text: text.rstrip(".").rstrip() + ".")


import time


def insert_annonations(driver, content):
    els = find_annotation_candidates(driver, content)
    for el in els:
        annon_el = get_annotation_el(driver, el)
        if annon_el:
            # general styling
            stylize_annotation(driver, annon_el)

            # wrap the element in a footnote before appending
            style_element(driver, annon_el, "footnote")

            # style the "keywords" in the main text
            style_element(driver, el, "annotated")

            # place the stylized annotation in the innerHTML of the
            # the original element
            append_to_inner_html(driver, el, annon_el.text)

            # Reset the page with the last clicked element
            driver.execute_script("arguments[0].click();", el)
            # time.sleep(0.350)

            try:
                WebDriverWait(driver,
                              ANIMATION_TIME_S).until_not(EC.presence_of_element_located((By.CLASS_NAME, "annotation")))
            except TimeoutException:
                raise TimeoutException(
                    f"Element was supposed to disappear, but did not within the specified time of `{ANIMATION_TIME_S}` seconds."
                )


def escape_hashtag(text):
    regex = re.compile(r"(?<!\\)#")
    return regex.sub(lambda match: r"\#", text)


def convert_raw_to_latex(driver, content, label_prefix):
    # This function scans and in-place modifies some html content
    # and then extracts a raw string version, with html tags replaced by latex-esque
    # syntax

    # Replace lines numbers with a latex label
    insert_line_labels(driver, content, label_prefix)
    # insert_word_labels(driver, content, label_prefix)

    # Place annotations as footnote
    insert_annonations(driver, content)

    # Handles tags for archaic words -> old and modern spelling
    insert_modern_english_overtext(driver, content)

    text = content.text
    # Some minor encapsulation (manually...cant use tex_escape anymore!)
    text = text.replace("&", "\&")

    # Replace \n with latex equivalent
    text = text.replace("\n", "\\\\")

    # Additionaly pass escaping # -- `fix` for book 6
    # Only match # not yet escaped!
    text = escape_hashtag(text)

    return text.encode("ascii", "ignore").decode()  # implicitly convert to latex and remove unicode (the hebrew...  )
