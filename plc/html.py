import json
from typing import Optional

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement


def wrap_inner_html(driver, el, front, back):
    old_text_raw = el.get_attribute("innerHTML")
    new_text = front + old_text_raw + back
    driver.execute_script(f"arguments[0].innerHTML = {json.dumps(new_text)};", el)


def append_to_inner_html(driver, el, text):
    old_text_raw = el.get_attribute("innerHTML")
    new_text = old_text_raw + text
    driver.execute_script(f"arguments[0].innerHTML = {json.dumps(new_text)};", el)


def replace_inner_html(driver, el, text):
    driver.execute_script(f"arguments[0].innerHTML = {json.dumps(text)};", el)


def modify_inner_html(driver, el, op):
    old_text_raw = el.get_attribute("innerHTML")
    new_text = op(old_text_raw)
    driver.execute_script(f"arguments[0].innerHTML = {json.dumps(new_text)};", el)


def get_inner_html_by_class(el: WebElement, class_name: str) -> Optional[str]:
    # Helper function that takes a WebElement and find a specific element by its class name and obtains the "innerHtml"
    # field which is a dartmouth page specific element type
    el = el.find_element(By.CLASS_NAME, class_name)
    try:
        return el.get_attribute("innerHTML")
    except NoSuchElementException:
        return None
