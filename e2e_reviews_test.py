import os
import sys
import django
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

USER_PASSWORD = os.getenv("E2E_USER_PASSWORD")
ADMIN_PASSWORD = os.getenv("E2E_ADMIN_PASSWORD")

if not USER_PASSWORD or not ADMIN_PASSWORD:
    sys.exit("E2E_USER_PASSWORD and E2E_ADMIN_PASSWORD are not set in the .env file.")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caloreat.settings")
django.setup()

from django.contrib.auth.models import User
from main.models import Reviews


def setup_users():
    user, _ = User.objects.get_or_create(username="burhan_test@example.com")
    user.email = "burhan_test@example.com"
    user.first_name = "Burhan Test"
    user.set_password(USER_PASSWORD)
    user.is_superuser = False
    user.is_staff = False
    user.save()

    admin, _ = User.objects.get_or_create(username="admin_test@example.com")
    admin.email = "admin_test@example.com"
    admin.first_name = "Admin Test"
    admin.set_password(ADMIN_PASSWORD)
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()

    Reviews.objects.filter(created_by__in=[user, admin]).delete()


def main():
    setup_users()

    options = webdriver.ChromeOptions()
    if "--headless" in sys.argv:
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    base_url = "http://127.0.0.1:8000"

    try:
        # Check Landing Page (Hero, Search, Education, Features, Reviews) as an anonymous visitor
        try:
            driver.get(f"{base_url}/")
        except Exception:
            print(f"Server is not running at {base_url}. Please run 'python manage.py runserver' first.")
            return

        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "hero")))
        assert "Your daily food compass" in driver.page_source
        assert driver.find_element(By.CSS_SELECTOR, "form.food-search input[name='q']")
        assert driver.find_element(By.ID, "education-title")
        assert driver.find_element(By.ID, "features-title")
        assert driver.find_element(By.ID, "reviews-title")

        # Clicking "Write a Review" while logged out should redirect to /login/
        write_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "add-reviews-button")))
        driver.execute_script("arguments[0].click();", write_btn)
        wait.until(EC.url_contains("/login/"))
        print("[PASS] Landing page and anonymous 'Write a Review' redirect verified")

        # Check CSRF token in the login form & log in as a regular user
        csrf = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-pane='login'] input[name='csrfmiddlewaretoken']")
            )
        )
        assert csrf.get_attribute("value")
        assert driver.get_cookie("csrftoken")
        print("[PASS] CSRF token and cookie verified")

        driver.find_element(By.ID, "login_username").send_keys("burhan_test@example.com")
        driver.find_element(By.ID, "login_password").send_keys(USER_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "div[data-pane='login'] button[type='submit']").click()

        wait.until(EC.url_to_be(f"{base_url}/"))
        wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "nav-user__name"), "Burhan Test"))
        assert driver.get_cookie("sessionid")
        assert driver.find_elements(By.ID, "selectAllReviewsBtn") == []
        print("[PASS] Regular user login and admin button restriction verified")

        # Add a new review via AJAX modal
        open_modal_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "add-reviews-button")))
        driver.execute_script("arguments[0].click();", open_modal_btn)
        wait.until(EC.visibility_of_element_located((By.ID, "reviewModal")))

        four_star_btn = driver.find_element(By.CSS_SELECTOR, "#starRatingPicker .star-rating-btn[data-rating='4']")
        four_star_btn.click()
        content_input = driver.find_element(By.ID, "content")
        content_input.clear()
        content_input.send_keys("E2E review from Burhan")
        driver.find_element(By.ID, "submitBtn").click()

        wait.until(
            EC.text_to_be_present_in_element((By.ID, "reviewCardsContainer"), "E2E review from Burhan")
        )
        print("[PASS] Regular user AJAX review creation verified")

        # Check 'My Review' filter and edit own review
        my_review_filter = driver.find_element(By.CSS_SELECTOR, "#reviewStarFilters button[data-mine='1']")
        driver.execute_script("arguments[0].click();", my_review_filter)
        wait.until(
            EC.text_to_be_present_in_element((By.ID, "reviewCardsContainer"), "E2E review from Burhan")
        )

        edit_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-update-review")))
        driver.execute_script("arguments[0].click();", edit_btn)
        wait.until(EC.visibility_of_element_located((By.ID, "reviewModal")))

        content_input = driver.find_element(By.ID, "content")
        content_input.clear()
        content_input.send_keys("E2E review from Burhan (Edited)")
        driver.find_element(By.ID, "submitBtn").click()

        wait.until(
            EC.text_to_be_present_in_element((By.ID, "reviewCardsContainer"), "E2E review from Burhan (Edited)")
        )
        print("[PASS] 'My Review' filter and review edit verified")

        # Log out regular user & log in as Superuser (Admin)
        logout_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.nav-logout")))
        driver.execute_script("arguments[0].click();", logout_btn)
        wait.until(EC.url_contains("/login/"))

        wait.until(EC.visibility_of_element_located((By.ID, "login_username"))).send_keys("admin_test@example.com")
        driver.find_element(By.ID, "login_password").send_keys(ADMIN_PASSWORD)
        driver.find_element(By.CSS_SELECTOR, "div[data-pane='login'] button[type='submit']").click()

        wait.until(EC.url_to_be(f"{base_url}/"))
        wait.until(EC.text_to_be_present_in_element((By.CLASS_NAME, "nav-user__name"), "Admin Test"))
        assert driver.find_elements(By.CLASS_NAME, "add-reviews-button") == []
        print("[PASS] Superuser login verified ('Write a Review' button hidden)")

        # Superuser Bulk Select & Bulk Delete review
        wait.until(
            EC.text_to_be_present_in_element((By.ID, "reviewCardsContainer"), "E2E review from Burhan (Edited)")
        )
        checkbox = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".review-select-checkbox"))
        )
        driver.execute_script("arguments[0].click();", checkbox)

        bulk_delete_btn = wait.until(EC.visibility_of_element_located((By.ID, "bulkDeleteReviewsBtn")))
        driver.execute_script("arguments[0].click();", bulk_delete_btn)
        wait.until(EC.alert_is_present()).accept()

        wait.until(
            lambda d: "E2E review from Burhan (Edited)" not in d.find_element(By.ID, "reviewCardsContainer").text
        )
        print("[PASS] Superuser bulk delete review verified")

        # Check Superuser logout and session cleanup
        logout_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.nav-logout")))
        driver.execute_script("arguments[0].click();", logout_btn)
        wait.until(EC.url_contains("/login/"))
        session_cookie = driver.get_cookie("sessionid")
        assert session_cookie is None or session_cookie["value"] == ""
        print("[PASS] Logout and session cleanup verified")

        print("\nAll Landing Page & Reviews E2E tests passed!")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
