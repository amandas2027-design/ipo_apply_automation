# apply_ipo.py
from playwright.sync_api import sync_playwright
import csv
import time
import os

# ============================================
# CONFIGURATION
# ============================================
IPO_NAME = "Kalinchock Hydropower  Limited"   #change this every time 
CSV_FILE = "users.csv"                        #csv file with credientials
SCREENSHOT_DIR = "debug_screenshots"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def find_and_click_apply(page, company_name):
    """Find company by name and click the Apply button."""
    try:
        print(f"   🔍 Searching for company: {company_name}")
        page.wait_for_selector(".company-list", timeout=30000)
        time.sleep(1)

        result = page.evaluate("""
            (targetCompany) => {
                const companyLists = document.querySelectorAll('.company-list');
                for (let companyBlock of companyLists) {
                    const nameSpan = companyBlock.querySelector(
                        'span[tooltip="Company Name"]'
                    );
                    if (nameSpan) {
                        const companyText = nameSpan.textContent.trim().toLowerCase();
                        const targetText  = targetCompany.trim().toLowerCase();
                        if (companyText.includes(targetText)
                            || targetText.includes(companyText)) {
                            const applyButton =
                                companyBlock.querySelector('button.btn-issue');
                            if (applyButton) {
                                applyButton.click();
                                return {
                                    found: true, clicked: true,
                                    companyName: nameSpan.textContent.trim()
                                };
                            } else {
                                return {
                                    found: true, clicked: false,
                                    companyName: nameSpan.textContent.trim(),
                                    error: "Apply button not found"
                                };
                            }
                        }
                    }
                }
                return { found: false, clicked: false, error: "Company not found" };
            }
        """, company_name)

        if result['found'] and result['clicked']:
            print(f"   ✅ Found '{result['companyName']}' — clicked Apply")
            return True
        elif result['found']:
            print(f"   ⚠️ Found '{result['companyName']}' but no Apply button")
            return False
        else:
            print(f"   ❌ Company '{company_name}' not found")
            list_available_companies(page)
            return False

    except Exception as e:
        print(f"   ❌ Error finding company: {e}")
        return False


def list_available_companies(page):
    """List available companies for debugging."""
    try:
        companies = page.evaluate("""
            () => {
                const items = document.querySelectorAll('.company-list');
                const names = [];
                items.forEach((item, i) => {
                    const s = item.querySelector('span[tooltip="Company Name"]');
                    const b = item.querySelector('button.btn-issue');
                    if (s) names.push({
                        index: i+1,
                        name: s.textContent.trim(),
                        hasApply: !!b
                    });
                });
                return names;
            }
        """)
        if companies:
            print("\n   📋 Available companies:")
            for c in companies:
                status = "✅" if c['hasApply'] else "❌"
                print(f"      {c['index']}. {c['name']} — {status}")
    except Exception as e:
        print(f"      Could not list companies: {e}")


def apply_ipo(page, user, company_name):
    """Apply for IPO for a single user (headless)."""
    try:
        print(f"\n{'='*55}")
        print(f"  Processing: {user['username']}")
        print(f"{'='*55}")

        # ==================== LOGIN ====================
        print("\n   📡 Step 1: Logging in...")
        print(f"      DP     : {user['dp']}")
        print(f"      User   : {user['username']}")

        page.click("#selectBranch")
        page.fill(".select2-search__field", user["dp"])
        page.keyboard.press("Enter")
        page.fill("#username", user["username"])
        page.fill("#password", user["password"])
        page.get_by_role("button", name="Login").click()

        print("      ⏳ Waiting for login response...")

        # ---------- CHECK LOGIN RESULT ----------
        try:
            page.wait_for_selector("text=My ASBA", timeout=15000)

            # ✅ LOGIN SUCCESS
            print("      ✅ LOGIN SUCCESSFUL!")
            print(f"      👤 Logged in as: {user['username']}")

            # Get current URL to confirm
            current_url = page.url
            print(f"      🌐 Current URL: {current_url}")

            # Try to grab the user's name from dashboard if visible
            try:
                name_element = page.query_selector(".user-name, .username, .nav-user")
                if name_element:
                    display_name = name_element.text_content().strip()
                    print(f"      📛 Display Name: {display_name}")
            except Exception:
                pass

        except Exception:
            # ❌ LOGIN FAILED
            print("      ❌ LOGIN FAILED!")
            print(f"      👤 User: {user['username']}")

            # Check for error messages on page
            try:
                error_element = page.query_selector(
                    ".alert-danger, .error-message, .toast-message, "
                    ".alert-warning, .error, .text-danger"
                )
                if error_element:
                    error_text = error_element.text_content().strip()
                    print(f"      ⚠️ Error Message: {error_text}")
                else:
                    print("      ⚠️ No error message found on page")
            except Exception:
                pass

            # Save screenshot for debugging
            fail_path = os.path.join(
                SCREENSHOT_DIR, f"login_fail_{user['username']}.png"
            )
            page.screenshot(path=fail_path)
            print(f"      📸 Screenshot saved: {fail_path}")
            print(f"      🔄 Skipping this user...\n")
            return False

        # ==================== NAVIGATE TO ASBA ====================
        print("\n   📡 Step 2: Navigating to My ASBA...")
        page.click("text=My ASBA")
        time.sleep(2)
        print("      ✅ Opened My ASBA page")

        # ==================== FIND & APPLY ====================
        print("\n   📡 Step 3: Finding company & clicking Apply...")
        if not find_and_click_apply(page, company_name):
            print(f"      ⚠️ Skipping {user['username']}")
            try:
                page.locator('a[tooltip="Logout"]').click()
                time.sleep(1)
            except Exception:
                pass
            return False

        time.sleep(1)

        # ==================== SELECT BANK ====================
        print("\n   📡 Step 4: Selecting bank...")
        page.evaluate("""
            () => {
                const sel = document.querySelector('#selectBank');
                if (sel) {
                    for (let opt of sel.options) {
                        if (opt.value && opt.value !== '' && !opt.disabled) {
                            sel.value = opt.value;
                            sel.dispatchEvent(new Event('change', {bubbles:true}));
                            break;
                        }
                    }
                }
            }
        """)
        time.sleep(1)
        print("      ✅ Bank selected")

        # ==================== SELECT ACCOUNT ====================
        print("\n   📡 Step 5: Selecting account...")
        page.evaluate("""
            () => {
                const sel = document.querySelector('#accountNumber');
                if (sel) {
                    for (let opt of sel.options) {
                        if (opt.value && opt.value !== '' && !opt.disabled) {
                            sel.value = opt.value;
                            sel.dispatchEvent(new Event('change', {bubbles:true}));
                            break;
                        }
                    }
                }
            }
        """)
        time.sleep(1)
        print("      ✅ Account selected")

        # ==================== FILL FORM ====================
        print("\n   📡 Step 6: Filling application form...")
        page.fill('[placeholder="Enter Applied Kitta Number"]', user["kitta"])
        print(f"      📝 Kitta: {user['kitta']}")
        page.fill('[placeholder="Enter CRN"]', user["crn"])
        print(f"      📝 CRN: {user['crn']}")
        page.check("#disclaimer")
        print("      ☑️  Disclaimer checked")
        page.click("text=Proceed")
        time.sleep(1)
        print("      ✅ Form filled & proceeded")

        # ==================== PIN & SUBMIT ====================
        print("\n   📡 Step 7: Submitting application...")
        page.fill("#transactionPIN", user["Pin"])
        print("      🔐 PIN entered")
        page.get_by_role("button", name="Apply").click()
        time.sleep(2)

        # ---------- CHECK SUBMISSION RESULT ----------
        try:
            # Check for success message
            success_element = page.query_selector(
                ".alert-success, .toast-success, .success-message"
            )
            if success_element:
                success_text = success_element.text_content().strip()
                print(f"      🎉 Server Response: {success_text}")
        except Exception:
            pass

        print(f"\n   🎉 SUCCESSFULLY APPLIED for {user['username']}!")

        # ==================== LOGOUT ====================
        print("\n   📡 Step 8: Logging out...")
        page.locator('a[tooltip="Logout"]').click()
        time.sleep(1)
        print("      ✅ Logged out")

        return True

    except Exception as e:
        print(f"\n   ❌ ERROR for {user['username']}: {e}")
        # Save error screenshot
        try:
            err_path = os.path.join(
                SCREENSHOT_DIR, f"error_{user['username']}.png"
            )
            page.screenshot(path=err_path)
            print(f"      📸 Error screenshot: {err_path}")
            page.locator('a[tooltip="Logout"]').click()
        except Exception:
            pass
        return False


def main():
    print("\n" + "=" * 60)
    print("  🚀 MeroShare IPO Auto-Apply  (HEADLESS / BACKGROUND)")
    print("=" * 60)
    print(f"  📌 Target Company : {IPO_NAME}")
    print(f"  📁 CSV File       : {CSV_FILE}")
    print(f"  📂 Debug Folder   : {os.path.abspath(SCREENSHOT_DIR)}")
    print(f"  🖥️  Mode           : Background (no browser window)")
    print("=" * 60 + "\n")

    success_count = 0
    fail_count = 0
    results = []  # Track per-user results

    with sync_playwright() as p:
        # =============================================
        # HEADLESS = TRUE → No browser window opens
        # =============================================
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        print("  🌐 Browser launched in background (headless)")

        # Load users
        try:
            with open(CSV_FILE) as f:
                users = list(csv.DictReader(f))
            print(f"  📊 Loaded {len(users)} users from CSV\n")
        except FileNotFoundError:
            print(f"  ❌ CSV not found: {CSV_FILE}")
            return
        except Exception as e:
            print(f"  ❌ CSV error: {e}")
            return

        # Navigate to MeroShare
        print("  🌐 Opening MeroShare login page...")
        page.goto(
            "https://meroshare.cdsc.com.np/#/login",
            wait_until="networkidle",
        )
        print("  ✅ Login page loaded\n")

        # Process each user
        for index, user in enumerate(users, 1):
            print(f"\n  📍 User {index} of {len(users)}")

            result = apply_ipo(page, user, IPO_NAME)

            if result:
                success_count += 1
                results.append({"user": user["username"], "status": "✅ Success"})
            else:
                fail_count += 1
                results.append({"user": user["username"], "status": "❌ Failed"})

            time.sleep(1)

        # ==================== FINAL SUMMARY ====================
        print("\n\n" + "=" * 60)
        print("  📊 FINAL SUMMARY")
        print("=" * 60)
        print(f"  ✅ Successful : {success_count}")
        print(f"  ❌ Failed     : {fail_count}")
        print(f"  📋 Total      : {len(users)}")
        print("-" * 60)

        # Per-user results table
        print(f"  {'Username':<25} {'Status'}")
        print(f"  {'-'*25} {'-'*15}")
        for r in results:
            print(f"  {r['user']:<25} {r['status']}")

        print("=" * 60)
        print("  🏁 All done! Browser closed.\n")

        browser.close()


if __name__ == "__main__":
    main()
