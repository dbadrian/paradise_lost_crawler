#!/usr/bin/env python

import argparse
from pathlib import Path
import json
from typing import Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from tqdm import tqdm

from plc.consts import PARADISE_LOST_LINKS
from plc.html import get_inner_html_by_class
from plc.latex import convert_raw_to_latex

DRIVER_MAP = {
    "firefox": (webdriver.Firefox, FirefoxOptions),
    "chrome": (webdriver.Chrome, ChromeOptions),
    # "phantomjs": (webdriver.PhantomJS, PHJOptions),
}

def setup_webdriver(driver_type):
    # create a headless instance of the selected driver type
    try:
        driver_cls, options_cls = DRIVER_MAP[driver_type]
    except KeyError:
        raise NotImplementedError(f"Chosen driver_type `{driver_type}` is not supported by selenium or plc.")

    options = options_cls()
    options.add_argument('-headless')
    driver = driver_cls(options=options)

    return driver    

def find_main_body_elements(main_el):
    # essentially all paragraphs, except the first one which is the argument
    els = main_el.find_elements(By.TAG_NAME, "p")[1:]
    return els

def crawl_page(page_name: str, link: str):
    # obtain a selenium webdriver
    driver = setup_webdriver(args.driver) 
    
    print(f"  - Crawling {page_name}")
    
    # make initial request
    driver.get(link)
    
    # find the content element, which contains both the argument (beginning paragraph the each book)
    # and the complete text body
    try:
        main_el = driver.find_element(By.ID, "content")
    except NoSuchElementException:
        raise NoSuchElementException("Couldn't find the `content` div. Something must have changed on the website layout.")
    
    
    raw_content = {}
    
    print(f"    -- meta data")
    # First we crawl the main meta data
    raw_content["title"] = get_inner_html_by_class(main_el, "msubhead") 
    raw_content["subtitle"] = get_inner_html_by_class(main_el, "msubsubhead")
    
    # Next, each books page has a preceeding `argument`
    # This already contains modern writing tooltips for archaic words, as well as interactive
    # javascript annotations.
    # Thus we need to use the more complex parsing pipeline where we directly convert the raw html
    # to a safe and escaped latex format
    print(f"    -- argument")
    argument_el = main_el.find_element(By.CLASS_NAME, "margument")
    raw_content["argument"] = convert_raw_to_latex(driver, argument_el, page_name)
    raw_content["main"] = []

    
    print(f"    -- content")
    for p in tqdm(find_main_body_elements(main_el), desc="Paragraph"):
        raw_content["main"].append(convert_raw_to_latex(driver, p, page_name))
  
        
        
    # title_el = driver.find_element(By.CLASS_NAME, "title")
    # raw_content["end"] = get_inner_html_by_class(title_el, "mi")
    # return raw_content


def main(args):
    print(":: Creating Output Folder")
    p_out = args.output
    p_json = p_out.joinpath("json")
    p_tex = p_out.joinpath("tex")
    p_json.mkdir(parents=True, exist_ok=True)
    p_tex.mkdir(parents=True, exist_ok=True)
    
    for idx, (name, link) in enumerate(PARADISE_LOST_LINKS.items()):
        crawl_page(name, link)
        break
    
    
    # driver = None
    # try:
                   
    #     for idx, (name, link) in enumerate(PARADISE_LOST.items()):
    #         if driver is None:
                

    #         fn_content = p_json.joinpath(f"{name}.json")
    #         if not fn_content.exists() or args.force:
    #             print(f" - Crawling and Preprocesing {name}")
    #             book = crawl_site(link, driver, name)
    #             # write "incremental" results
    #             with open(fn_content, "w") as f:
    #                 json.dump(book, f)
    #         else:
    #             print(f"`{name}` already crawled. Skipping. Use '-f,--force' to recrawl.")

    #     for idx, (name, _) in enumerate(PARADISE_LOST.items()):
    #         fn_content = p_json.joinpath(f"{name}.json")
    #         with open(fn_content, "r") as f:
    #             content = json.load(f)
    #         render_latex(p_tex.joinpath(f"{name}.tex"), content)

    #     files = {"files": [f"{name}.tex" for name in PARADISE_LOST.keys()]}
    #     render_latex(p_tex.joinpath(f"content.tex"), files, template="content.tpl")

    #     render_latex(p_tex.joinpath(f"main.tex"),
    #                 {
    #                     "force_modern_spelling": args.force_modern_spelling,
    #                     "disable_modern_spelling": args.disable_modern_spelling,
    #                     "disable_annotations": args.disable_annotations
    #                 },
    #                 template="main.tpl")
    # except KeyboardInterrupt:
    #     # I know...signal should be handled properly
    #     print("!! Emergency Shutdown !!")
    #     if driver:
    #         driver.quit()

    # if driver:
    #     driver.quit()



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", type=Path, required=True)
    parser.add_argument(
        "--driver",
        "-d",
        type=str,
        default="firefox",
        help="firefox or chrome supported", # TODO: auto generate the list
        required=False,
    )
    parser.add_argument("--force", "-f", default=False, action="store_true")
    parser.add_argument("--disable-annotations", default=False, action="store_true")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--disable-modern-spelling", default=False, action="store_true")
    group.add_argument("--force-modern-spelling", default=False, action="store_true")

    args = parser.parse_args()
    main(args)