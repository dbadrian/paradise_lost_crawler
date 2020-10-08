#!/usr/bin/env python
import argparse
import json
from pathlib import Path
import re
import os
import logging
from string import punctuation
import signal
import sys
from jinja2 import Template, Environment, FileSystemLoader

import selenium
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

# from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options
from tqdm import tqdm

from crawler.links import PARADISE_LOST, PARADISE_REGAINED
from crawler.latex import convert_raw_to_latex


ENV_ARGS = {
    'block_start_string': '\BLOCK{',
    'block_end_string': '}',
    'variable_start_string': '\VAR{',
    'variable_end_string': '}',
    'comment_start_string': '\#{',
    'comment_end_string': '}',
    'line_statement_prefix': '%-',
    'line_comment_prefix': '%#',
    'trim_blocks': True,
    'autoescape': False,
}


PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_ENVIRONMENT = Environment(
	variable_start_string = '$$',
	variable_end_string = '$$',
    autoescape=False,
    loader=FileSystemLoader(os.path.join(PATH, 'template')),
    trim_blocks=True,
    lstrip_blocks=True)


def setup_webdriver(driver_type="firefox"):
    options = Options()
    options.add_argument("--headless")

    if driver_type == "firefox":
        driver = webdriver.Firefox(firefox_options=options)
    elif driver_type == "phantomjs":
        driver = webdriver.PhantomJS()  # headless alternative
    else:
        raise NotImplementedError(f"Unknown driver type {driver_type}")

    return driver


def get_inner_html_by_class(el, class_name):
    el = el.find_element_by_class_name(class_name)
    try:
        return el.get_attribute("innerHTML")
    except selenium.common.exceptions.NoSuchElementException:
        return None


def crawl_content(main_el):
    els = main_el.find_elements_by_tag_name("p")[1:]
    return els


def crawl_site(link, driver, PREFIX):
    driver.get(link)
    main_el = driver.find_element_by_id("content")

    raw_content = {}
    raw_content["title"] = get_inner_html_by_class(main_el, "msubhead") 
    raw_content["subtitle"] = get_inner_html_by_class(main_el, "msubsubhead")
    raw_content["argument"] = convert_raw_to_latex(
        driver, main_el.find_elements_by_class_name("margument")[0], PREFIX
    )
    raw_content["main"] = []
    for p in tqdm(crawl_content(main_el)):
        raw_content["main"].append(convert_raw_to_latex(driver, p, PREFIX))
    title_el = driver.find_element_by_class_name("title")
    raw_content["end"] = get_inner_html_by_class(title_el, "mi")
    return raw_content


def render_template(template_filename, context):
    return TEMPLATE_ENVIRONMENT.get_template(template_filename).render(context)


def render_latex(p_out, content, template='book.tpl'):
    with open(p_out, 'w') as f:
        tex = render_template(template, content)
        f.write(tex)

def main(args):
    driver = None
    try:
        print(":: Creating Output Folder")
        p_out = args.output
        p_out.mkdir(parents=True, exist_ok=True)
        fn_content = p_out.joinpath("content.json")
        if not fn_content.exists() or args.force:
            # Obtain Driver
            print(":: Obtaining Driver")
            driver = setup_webdriver(args.driver)

            book = {}
            
            for idx, (name, link) in enumerate(PARADISE_LOST.items()):
                print(f" - Parsing {name}")
                book[name] = crawl_site(link, driver, name)
                # write "incremental" results
                with open(fn_content, "w") as f:
                    json.dump(book, f)
                break
        else:
            print("Skipping crawling")

        with open(fn_content, "r") as f:
            content = json.load(f)
        for idx, (name, _) in enumerate(PARADISE_LOST.items()):
            render_latex(p_out.joinpath(f"{name}.tex"), content[name])
            break

        files = {"files": [f"{name}.tex" for name in content.keys()]}
        render_latex(p_out.joinpath(f"content.tex"), files, template="content.tpl")

    except KeyboardInterrupt:
        # I know...signal should be handled properly
        print("!! Emergency Shutdown !!")
        if driver:
            driver.quit()

    if driver:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument(
        "--driver",
        "-d",
        type=str,
        default="firefox",
        help="Phantomjs, Chrome, Firefox supported",
        required=False,
    )
    parser.add_argument("--force", "-f", default=False, action="store_true")
    args = parser.parse_args()
    main(args)
