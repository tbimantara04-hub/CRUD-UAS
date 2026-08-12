# =============================================================================
# Author      : Satria Tegar Bimantara
# Course      : Pengujian Perangkat Lunak
# Institution : Politeknik Siber dan Sandi Negara
# Subject     : UAS — Automation Testing DamnCRUD Application
# Repository  : https://github.com/tbimantara04-hub/CRUD-UAS
# Description : Skrip otomasi Selenium WebDriver berbasis Pytest untuk
#               memverifikasi operasi CRUD pada aplikasi DamnCRUD.
#               Menjalankan 5 fungsional test case secara paralel.
# =============================================================================

import pytest
import time
import uuid
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

# =============================================================================
# KONFIGURASI GLOBAL
# =============================================================================
BASE_URL = os.getenv("BASE_URL", "http://localhost/DamnCRUD")
LOGIN_URL = f"{BASE_URL}/login.php"
CREATE_URL = f"{BASE_URL}/create.php"
READ_URL = f"{BASE_URL}/index.php"

VALID_USERNAME = "admin"
VALID_PASSWORD = "nimda666!"

DEFAULT_TIMEOUT = 15


def _get_unique_contact_name():
    return f"Auto-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Wajib untuk CI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")

    driver_instance = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), 
        options=chrome_options
    )
    driver_instance.implicitly_wait(5)
    yield driver_instance
    driver_instance.quit()


@pytest.fixture(scope="function")
def authenticated_driver(driver):
    _perform_login(driver, VALID_USERNAME, VALID_PASSWORD)
    return driver


def _perform_login(driver, username, password):
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, DEFAULT_TIMEOUT)

    if "index.php" in driver.current_url and "login.php" not in driver.current_url:
        return

    username_field = wait.until(
        EC.presence_of_element_located((By.ID, "inputUsername"))
    )
    username_field.clear()
    username_field.send_keys(username)

    password_field = driver.find_element(By.ID, "inputPassword")
    password_field.clear()
    password_field.send_keys(password)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    wait.until(EC.url_contains("index.php"))


def _navigate_to_create(driver):
    driver.get(CREATE_URL)
    WebDriverWait(driver, DEFAULT_TIMEOUT).until(
        EC.presence_of_element_located((By.XPATH, "//form"))
    )


def _get_table_rows(driver) -> list:
    wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    return driver.find_elements(By.XPATH, "//table/tbody/tr | //table/tr[position()>1]")


class TestDamnCRUDFunctionality:

    def test_TC001_create_contact_with_valid_data(self, authenticated_driver):
        driver = authenticated_driver
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
        contact_name = _get_unique_contact_name()
        _navigate_to_create(driver)

        name_field = wait.until(EC.presence_of_element_located((By.NAME, "name")))
        name_field.send_keys(contact_name)
        driver.find_element(By.NAME, "phone").send_keys("081234567890")
        driver.find_element(By.NAME, "email").send_keys(f"{contact_name.lower()}@example.com")
        driver.find_element(By.NAME, "title").send_keys("Testing")

        driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']").click()
        wait.until(EC.url_contains("index.php"))
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        assert contact_name in driver.page_source

    def test_TC002_read_contact_list_displays_correctly(self, authenticated_driver):
        driver = authenticated_driver
        driver.get(READ_URL)
        rows = _get_table_rows(driver)
        assert len(rows) > 0

    def test_TC003_update_contact_phone_number(self, authenticated_driver):
        driver = authenticated_driver
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
        contact_name = _get_unique_contact_name()
        updated_phone = "089999888777"

        # Setup data
        _navigate_to_create(driver)
        wait.until(EC.presence_of_element_located((By.NAME, "name"))).send_keys(contact_name)
        driver.find_element(By.NAME, "phone").send_keys("081234567890")
        driver.find_element(By.NAME, "email").send_keys(f"{contact_name.lower()}@example.com")
        driver.find_element(By.NAME, "title").send_keys("Testing")
        driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']").click()
        wait.until(EC.url_contains("index.php"))
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        # Klik Edit
        edit_link = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//tr[contains(., '{contact_name}')]//a[contains(@href, 'update.php')]")
            )
        )
        edit_link.click()

        # Update phone
        phone_field = wait.until(EC.presence_of_element_located((By.NAME, "phone")))
        phone_field.clear()
        phone_field.send_keys(updated_phone)
        driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']").click()
        wait.until(EC.url_contains("index.php"))
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        assert updated_phone in driver.page_source

    def test_TC004_delete_contact_removes_from_list(self, authenticated_driver):
        driver = authenticated_driver
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
        contact_name = _get_unique_contact_name()

        # Setup data
        _navigate_to_create(driver)
        wait.until(EC.presence_of_element_located((By.NAME, "name"))).send_keys(contact_name)
        driver.find_element(By.NAME, "phone").send_keys("081234567890")
        driver.find_element(By.NAME, "email").send_keys(f"{contact_name.lower()}@example.com")
        driver.find_element(By.NAME, "title").send_keys("Testing")
        driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']").click()
        wait.until(EC.url_contains("index.php"))
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        # Klik Delete
        delete_link = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//tr[contains(., '{contact_name}')]//a[contains(@href, 'delete.php')]")
            )
        )
        delete_link.click()

        try:
            alert = WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert.accept()
        except TimeoutException:
            pass

        wait.until(EC.staleness_of(delete_link))
        time.sleep(1)
        assert contact_name not in driver.page_source

    def test_TC005_create_contact_fails_with_empty_name(self, authenticated_driver):
        driver = authenticated_driver
        wait = WebDriverWait(driver, DEFAULT_TIMEOUT)
        _navigate_to_create(driver)

        phone_field = wait.until(EC.presence_of_element_located((By.NAME, "phone")))
        phone_field.send_keys("081111222333")
        driver.find_element(By.NAME, "email").send_keys("validasi@example.com")
        driver.find_element(By.NAME, "title").send_keys("Testing")
        driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']").click()

        time.sleep(1)
        assert "create.php" in driver.current_url
