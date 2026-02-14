import sys
from time import sleep
from typing import Dict, List, Set

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException


DEFAULT_URL = "https://socal.eosfitness.com/westcovina-guest-vip"

# Default values to type into detected fields
DEFAULT_VALUES = {
    "dob": "02/05/2004",
    "first": "Michael",
    "last": "Tse",
    "phone": "626-367-8923",
    "email": "mmtse12@gmail.com",
    "gender": "Male",
    "street": "38 east forest ave",
    "city": "Arcadia",
    "state": "CA",
    "postal": "91006",
    "goal": "Gain Muscle/Weight",
}


FIELD_KEYWORDS: Dict[str, List[str]] = {
    "dob": ["dob", "dateofbirth", "birth", "birthday", "date"],
    "first": ["first", "given"],
    "last": ["last", "surname", "family"],
    "phone": ["phone", "mobile", "cell", "tel"],
    "email": ["email", "e-mail", "mail"],
    "gender": ["gender", "sex"],
    "street": ["address", "street", "addr"],
    "city": ["city", "town"],
    "state": ["state", "region", "province"],
    "postal": ["zip", "postal", "postcode", "postalcode"],
    "goal": ["goal", "fitness", "fitness goal", "reg. fitness", "reg", "guest reg"],
}


def normalize(s: str) -> str:
    return (s or "").lower().strip()


def element_signatures(driver, elem) -> str:
    parts: List[str] = []
    try:
        parts.append(elem.get_attribute("name") or "")
        parts.append(elem.get_attribute("id") or "")
        parts.append(elem.get_attribute("placeholder") or "")
        parts.append(elem.get_attribute("aria-label") or "")
        parts.append(elem.get_attribute("title") or "")
        parts.append(elem.get_attribute("class") or "")
    except Exception:
        pass

    # try to find associated <label for="id"> text
    try:
        eid = elem.get_attribute("id")
        if eid:
            labels = driver.find_elements(By.XPATH, f"//label[@for='{eid}']")
            for l in labels:
                try:
                    parts.append(l.text or "")
                except Exception:
                    pass
    except Exception:
        pass

    # also include visible surrounding text (small heuristic)
    try:
        txt = elem.text
        if txt:
            parts.append(txt)
    except Exception:
        pass

    return " ".join(parts)


def find_field_for_keywords(driver, wait: WebDriverWait, keywords: List[str], used: Set[str]) -> object:
    elems = driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
    for e in elems:
        try:
            sig = normalize(element_signatures(driver, e))
        except Exception:
            sig = ""
        if not sig:
            continue
        if e.id in used if hasattr(e, 'id') else False:
            pass
        # match any keyword
        for kw in keywords:
            if kw in sig:
                # avoid returning same element twice via its id or xpath
                try:
                    uid = e.get_attribute("id") or e.get_attribute("name") or e.get_attribute("placeholder") or e.get_attribute("aria-label")
                except Exception:
                    uid = None
                if uid and uid in used:
                    break
                return e
    return None


def choose_radio_by_label(driver, name_keyword: str, value_preference: str = "Male"):
    radios = driver.find_elements(By.CSS_SELECTOR, "input[type=radio]")
    for r in radios:
        try:
            sig = normalize(element_signatures(driver, r))
            if name_keyword in sig:
                # choose option whose value or label matches preference
                val = (r.get_attribute("value") or "")
                if normalize(val) == normalize(value_preference):
                    if not r.is_selected():
                        r.click()
                    return True
        except Exception:
            continue
    # fallback: click first radio that matches keyword
    for r in radios:
        try:
            sig = normalize(element_signatures(driver, r))
            if name_keyword in sig:
                if not r.is_selected():
                    r.click()
                return True
        except Exception:
            continue
    return False


def choose_option_for_field(driver, keywords: List[str], value_preference: str) -> bool:
    # Try radios first: find radio inputs whose signature includes a keyword
    radios = driver.find_elements(By.CSS_SELECTOR, "input[type=radio]")
    groups = {}
    for r in radios:
        try:
            sig = normalize(element_signatures(driver, r))
            for kw in keywords:
                if kw in sig:
                    name = r.get_attribute("name") or r.get_attribute("id") or "__no_name__"
                    groups.setdefault(name, []).append(r)
                    break
        except Exception:
            continue

    # For each group, try to find option matching value_preference
    for grp, opts in groups.items():
        for opt in opts:
            try:
                val = (opt.get_attribute("value") or "")
                # try nearby label text
                lab = ""
                try:
                    eid = opt.get_attribute("id")
                    if eid:
                        labels = driver.find_elements(By.XPATH, f"//label[@for='{eid}']")
                        lab = " ".join([l.text for l in labels if l.text])
                except Exception:
                    lab = ""
                if normalize(val) == normalize(value_preference) or (lab and normalize(lab) == normalize(value_preference)) or (normalize(value_preference) in normalize(val)) or (normalize(value_preference) in normalize(lab)):
                    if not opt.is_selected():
                        opt.click()
                    return True
            except Exception:
                continue

    # Try selects (dropdowns)
    selects = driver.find_elements(By.TAG_NAME, "select")
    for s in selects:
        try:
            sig = normalize(element_signatures(driver, s))
            for kw in keywords:
                if kw in sig:
                    options = s.find_elements(By.TAG_NAME, "option")
                    for opt in options:
                        try:
                            if normalize(opt.text) == normalize(value_preference) or normalize(opt.get_attribute("value") or "") == normalize(value_preference):
                                opt.click()
                                return True
                        except Exception:
                            continue
        except Exception:
            continue

    return False


def check_all_checkboxes_and_submit(driver):
    # Wait briefly for the consent page to render
    sleep(0.8)
    clicked_any = False

    try:
        boxes = driver.find_elements(By.CSS_SELECTOR, "input[type=checkbox]")
        for b in boxes:
            try:
                if not b.is_selected():
                    b.click()
                    clicked_any = True
            except Exception:
                continue
    except Exception:
        pass

    # Also handle elements styled as checkboxes with role=checkbox
    try:
        role_boxes = driver.find_elements(By.CSS_SELECTOR, "[role=checkbox]")
        for rb in role_boxes:
            try:
                aria = rb.get_attribute("aria-checked")
                if aria is None or aria.lower() in ("false", "0"):
                    rb.click()
                    clicked_any = True
            except Exception:
                try:
                    rb.click()
                    clicked_any = True
                except Exception:
                    continue
    except Exception:
        pass

    if not clicked_any:
        print("No checkboxes found to check (still attempting to submit).")

    # Try to find and click a final Submit button
    submit_btn = None
    try:
        candidates2 = ["submit", "finish", "confirm", "complete"]
        buttons = driver.find_elements(By.XPATH, "//button|//input[@type='submit']|//a")
        for b in buttons:
            try:
                txt = normalize(b.text or b.get_attribute("value") or b.get_attribute("aria-label") or "")
                for c in candidates2:
                    if c in txt:
                        submit_btn = b
                        break
                if submit_btn:
                    break
            except Exception:
                continue
    except Exception:
        pass

    if submit_btn:
        try:
            submit_btn.click()
            print("Clicked final Submit")
        except Exception:
            print("Found final submit but could not click it")
    else:
        print("No final Submit button found")


def fill_element(driver, elem, value: str):
    tag = elem.tag_name.lower()
    itype = (elem.get_attribute("type") or "").lower()
    try:
        if itype in ("radio", "checkbox"):
            if not elem.is_selected():
                elem.click()
            return True
        if tag == "select":
            # try to pick option by visible text
            options = elem.find_elements(By.TAG_NAME, "option")
            for opt in options:
                try:
                    if normalize(opt.text) == normalize(value) or normalize(opt.get_attribute("value")) == normalize(value):
                        opt.click()
                        return True
                except Exception:
                    continue
            # fallback: send keys
            elem.send_keys(value)
            return True
        # input/textarea
        try:
            elem.clear()
        except Exception:
            pass
        elem.send_keys(value)
        return True
    except Exception:
        return False


def auto_fill_form(url: str, values: Dict[str, str] = None, headless: bool = False):
    values = values or DEFAULT_VALUES

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 12)

    used_ids: Set[str] = set()

    try:
        driver.get(url)

        # small initial wait
        sleep(0.6)

        # Fill DOB first
        dob_elem = None
        try:
            # try obvious input[type=date]
            dob_elem = driver.find_element(By.CSS_SELECTOR, "input[type=date]")
        except Exception:
            pass
        if not dob_elem:
            dob_elem = find_field_for_keywords(driver, wait, FIELD_KEYWORDS["dob"], used_ids)
        if dob_elem:
            fill_element(driver, dob_elem, values.get("dob", ""))
            try:
                uid = dob_elem.get_attribute("id") or dob_elem.get_attribute("name")
                if uid:
                    used_ids.add(uid)
            except Exception:
                pass

        # Fill remaining fields using heuristics
        for key in ["first", "last", "phone", "email", "street", "city", "state", "postal"]:
            kw = FIELD_KEYWORDS.get(key, [])
            elem = find_field_for_keywords(driver, wait, kw, used_ids)
            if elem:
                success = fill_element(driver, elem, values.get(key, ""))
                try:
                    uid = elem.get_attribute("id") or elem.get_attribute("name")
                    if uid:
                        used_ids.add(uid)
                except Exception:
                    pass
                if not success:
                    print(f"Warning: couldn't fill {key}")
            else:
                print(f"Warning: field not found for {key}")

        # Gender radios handled separately
        # preferred value from values['gender']
        if not choose_radio_by_label(driver, "gender", values.get("gender", "Male")):
            # try matching radios by nearby labels
            choose_radio_by_label(driver, "sex", values.get("gender", "Male"))

        # Select fitness goal (e.g. "Gain Muscle/Weight") using heuristics
        if not choose_option_for_field(driver, FIELD_KEYWORDS.get("goal", []), values.get("goal", "")):
            # try alternate keyword
            choose_option_for_field(driver, ["fitness", "goal"], values.get("goal", ""))

        # try to find and click a Next/Submit button
        btn = None
        # common texts
        candidates = ["next", "continue", "submit", "join", "get pass", "get started"]
        try:
            # look for clickable buttons
            buttons = driver.find_elements(By.XPATH, "//button|//input[@type='submit']")
            for b in buttons:
                try:
                    txt = normalize(b.text or b.get_attribute("value") or "")
                    for c in candidates:
                        if c in txt:
                            btn = b
                            break
                    if btn:
                        break
                except Exception:
                    continue
        except Exception:
            pass

        if not btn:
            # fallback: first submit input or button
            try:
                btn = driver.find_element(By.CSS_SELECTOR, "button[type=submit], input[type=submit]")
            except Exception:
                btn = None

        if btn:
            try:
                btn.click()
                print("Clicked next/submit button")
                # After clicking next, attempt to check consent boxes and submit on next page
                check_all_checkboxes_and_submit(driver)
            except Exception:
                print("Found button but could not click it")
        else:
            print("No Next/Submit button found automatically")

        sleep(1.0)
        print("Auto-fill completed (heuristic-based).")

    finally:
        driver.quit()


def run_automation(url: str = DEFAULT_URL):
    """Run the automation for the given URL or default URL."""
    auto_fill_form(url)


def main():
    url = DEFAULT_URL
    if len(sys.argv) >= 2:
        url = sys.argv[1]
    run_automation(url)


if __name__ == "__main__":
    main()
