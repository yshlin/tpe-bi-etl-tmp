import os
import time
from selenium.webdriver import ActionChains, Firefox, FirefoxProfile
from selenium.webdriver.common.by import By
from argparse import ArgumentParser

from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from datetime import datetime, timedelta
import pandas as pd

from config import STRIPE_DOWNLOAD_DIR, STRIPE_URL, STRIPE_USERNAME, STRIPE_PASSWORD, STRIPE_PAYMENT_FILE, \
    STRIPE_DESTINATION


def get_arg_parser():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nofullscreen",
        default=False,
        action="store_true",
        help="The ETL task to run.",
    )
    parser.add_argument(
        "--norotate",
        default=False,
        action="store_true",
        help="Don't rotate between tabs.",
    )
    parser.add_argument(
        "--testreload",
        default=False,
        action="store_true",
        help="Test reload once.",
    )
    parser.add_argument(
        "--elem-wait",
        type=int,
        default=10,
        help="Seconds to wait for elements.",
    )
    parser.add_argument(
        "--rotate-wait",
        type=int,
        default=10,
        help="Seconds to wait for carousel rotation.",
    )
    parser.add_argument(
        "--load-wait",
        type=int,
        default=10,
        help="Seconds to wait for page load.",
    )
    parser.add_argument(
        "--reload-time",
        type=int,
        default=9,
        help="Day of hour to reload all charts.",
    )
    parser.add_argument(
        "--login-time",
        type=int,
        default=30,
        help="Seconds wait for manual login.",
    )
    return parser


class StripeDashboard:

    def __init__(self, wait_sec, nofullscreen, reload_hour, login_time,
                 load_wait):
        profile = FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", STRIPE_DOWNLOAD_DIR)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
        options = Options()
        # options.headless = True
        self.browser = Firefox(firefox_profile=profile, options=options)
        if not nofullscreen:
            self.browser.fullscreen_window()
        self.actions = ActionChains(self.browser)
        self.wait = WebDriverWait(self.browser, wait_sec)
        self.longwait = WebDriverWait(self.browser, 600)
        self.reload_hour = reload_hour
        self.last_reload = datetime.now()
        self.load_wait = load_wait
        self.logins = []
        self.login_time = login_time
        self.extract_report()

    def wait_elem_presence(self, by, selector, longwait=False):
        if longwait:
            return self.longwait.until(
                ec.presence_of_element_located((by, selector))
            )
        else:
            return self.wait.until(
                ec.presence_of_element_located((by, selector))
            )

    def extract_report(self, login=True):
        self.browser.get(STRIPE_URL)

        if login:
            # auto login
            time.sleep(1)
            email = self.wait_elem_presence(By.CSS_SELECTOR, '#email')
            for c in STRIPE_USERNAME:
                email.send_keys(c)
                time.sleep(0.3)
            passwd = self.wait_elem_presence(By.CSS_SELECTOR, '#old-password')
            for c in STRIPE_PASSWORD:
                passwd.send_keys(c)
                time.sleep(0.3)
            time.sleep(1)
            submit = self.wait_elem_presence(By.CSS_SELECTOR, 'button[type=submit]')
            submit.click()
            # manual login
            # time.sleep(self.login_time)

        export_button = self.wait_elem_presence(
            By.XPATH, '//button[@data-db-analytics-name="list_views.header.export.filter"]')
        export_button.click()

        timezone_radio = self.wait_elem_presence(By.CSS_SELECTOR, "input[name=timezone][value='Etc/UTC']")
        timezone_radio.click()

        period_radio = self.wait_elem_presence(By.CSS_SELECTOR, 'input[name="range"][value="previous7"]')
        period_radio.click()

        col_select = self.wait_elem_presence(By.CSS_SELECTOR, '.Select-element')
        col_select.click()

        col_option = self.wait_elem_presence(By.CSS_SELECTOR, '.Select-element > option[value="custom"]')
        col_option.click()
        uncheck_cols = ['customer_email-checkbox', 'captured-checkbox', 'card_id-checkbox', 'invoice_id-checkbox', 'transfer-checkbox']
        for uncheck_col in uncheck_cols:
            check = self.wait_elem_presence(By.CSS_SELECTOR, '#%s' % uncheck_col)
            check.click()
        export_button2 = self.wait_elem_presence(By.CSS_SELECTOR, '.ButtonGroup > div > div:nth-child(2) button')
        export_button2.click()
        download_button = self.wait_elem_presence(By.CSS_SELECTOR, '.ButtonLink-label', True)
        print(self.browser.current_url)

    def staystill(self):
        time.sleep(10*30)

    def shutdown(self):
        self.browser.quit()


def extract_load_daily_files():
    df = pd.read_csv(STRIPE_PAYMENT_FILE)
    df['created_date'] = pd.to_datetime(df['Created (UTC)'].str.slice(0, 10))
    dates = df['created_date'].unique()
    for dt in dates:
        df[df['created_date'] == dt].to_csv('./stripe/unified_payments_%s.csv' % str(dt)[:10], index=False)
        os.system('gsutil cp ./stripe/unified_payments_%s.csv %s' % (str(dt)[:10], STRIPE_DESTINATION))


def main():
    os.system('rm %s' % STRIPE_PAYMENT_FILE)
    args = get_arg_parser().parse_args()
    stripe = StripeDashboard(wait_sec=args.elem_wait,
                               nofullscreen=args.nofullscreen,
                               reload_hour=args.reload_time,
                               login_time=args.login_time,
                               load_wait=args.load_wait)
    stripe.staystill()
    stripe.shutdown()
    extract_load_daily_files()


if __name__ == "__main__":
    main()
