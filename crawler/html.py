import json


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
