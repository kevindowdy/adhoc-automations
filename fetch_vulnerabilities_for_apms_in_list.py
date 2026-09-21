# This script is designed to download the vulnerabilities for a specific list of APMs
#     Filter only on APM, SDLC Status, Severity
from playwright.sync_api import sync_playwright
import time
import logging
import traceback
from datetime import datetime
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

USERNAME = "fbfepde"  # Replace with username

APM_VALUES = ["APM0008659", "APM0004316", "APM0003782", "APM0003334", "APM0006087", "APM0003119", "APM0005271", "APM0003624", "APM0004192", "APM0003606", "APM0003324", "APM0004169", "APM0003416", "APM0003153", "APM0003145", "APM0003424", "APM0004383", "APM0004288", "APM0003375", "APM0003750", "APM0003405", "APM0003134", "APM0005334", "APM0003121", "APM0004161", "APM0003234", "APM0006014", "APM0003646", "APM0010996", "APM0004335", "APM0003254", "APM0006543", "APM0003660", "APM0004671", "APM0010997", "APM0004668"]

SEVERITY_VALUES = ["Low", "Critical", "High", "Medium"]
SDLC_STATUS_VALUES = ["(Not Set)", "Production", "Production (Old Version)"]

DASHBOARD_URL = (
    "https://saltminer.fiserv.one/s/open-sdlc-vulns-reporting-dashboard/app/dashboards"
    "#/view/3535dff0-8892-11ee-8c18-3fd35c13de64?_g=(filters:!())&embed=true"
)

STORAGE_STATE_PATH = Path(
    fr"C:\Users\{USERNAME}\Documents\Temporary\FIG_Storage_State\storage_state.json"
)

todays_date = datetime.today().strftime("%Y%m%d")

APP_NAME = "fetch-open-vulnerabilities"

# =============================================================================
# LOGGING
# =============================================================================

LOG_FILE = (
    fr"C:\Users\{USERNAME}\Documents\Temporary\FIG_App_Logs"
    fr"\saltminer_download_{datetime.now().strftime('%Y%m%d')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format=f'{{"timestamp":"%(asctime)s","level":"%(levelname)s","message":"%(message)s","application":"{APP_NAME}"}}',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# =============================================================================
# HELPERS
# =============================================================================

def select_multiple_values(selector, values, wait_seconds=20):
    """
    Select multiple values from a Kibana filter control.
    """
    for item in values:
        logger.info(f"Selecting value: {item}")

        selector.click()
        selector.press_sequentially(item)

        logger.info(
            f"Waiting {wait_seconds} seconds for search results ({item})"
        )
        time.sleep(wait_seconds)

        selector.press("ArrowDown")
        selector.press("Enter")

        logger.info(f"Successfully selected: {item}")


# =============================================================================
# MAIN
# =============================================================================

browser = None
context = None
page = None

try:

    logger.info("=" * 80)
    logger.info("Fetch-Open-Vulnerabilities SCRIPT STARTED")
    logger.info(f"APM Values: {APM_VALUES}")
    logger.info(f"Severity Values: {SEVERITY_VALUES}")
    logger.info(f"SDLC Status Values: {SDLC_STATUS_VALUES}")

    script_start = time.time()

    with sync_playwright() as p:

        logger.info("Launching Chrome browser")

        browser = p.chromium.launch(
            executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
            headless=False,
        )

        logger.info("Creating browser context")

        context = browser.new_context(
            accept_downloads=True,
            storage_state=str(STORAGE_STATE_PATH),
        )

        page = context.new_page()

        # ---------------------------------------------------------------------
        # LOGIN
        # ---------------------------------------------------------------------

        logger.info("Navigating to dashboard")
        page.goto(DASHBOARD_URL)

        logger.info("Clicking 'Log in with SSO'")
        page.get_by_text("Log in with SSO").click()

        logger.info("Waiting 45 seconds for authentication")
        time.sleep(45)

        # ---------------------------------------------------------------------
        # APM FILTER
        # ---------------------------------------------------------------------

        logger.info("Applying APM filter(s)")

        apm_selector = page.get_by_label(
            "APM Number",
            exact=True
        )

        select_multiple_values(
            apm_selector,
            APM_VALUES
        )

        # ---------------------------------------------------------------------
        # SEVERITY FILTERS
        # ---------------------------------------------------------------------

        logger.info(
            f"Applying Severity filters: {SEVERITY_VALUES}"
        )

        severity_selector = page.get_by_label(
            "Issue Severity",
            exact=True
        )

        select_multiple_values(
            severity_selector,
            SEVERITY_VALUES
        )

        # ---------------------------------------------------------------------
        # SDLC STATUS FILTERS
        # ---------------------------------------------------------------------

        logger.info(
            f"Applying SDLC Status filters: {SDLC_STATUS_VALUES}"
        )

        sdlc_selector = page.get_by_label(
            "SDLC Status",
            exact=True
        )

        select_multiple_values(
            sdlc_selector,
            SDLC_STATUS_VALUES
        )

        logger.info("Clicking Apply Now")
        page.locator(
            '[data-test-subj="inputControlSubmitBtn"]'
        ).click()

        logger.info("Waiting 60 seconds for dashboard refresh")
        time.sleep(60)

        # ---------------------------------------------------------------------
        # DOWNLOAD CSV
        # ---------------------------------------------------------------------

        logger.info("Finding Open SDLC dashboard panel")

        panel = page.get_by_role(
            "figure",
            name="Dashboard panel: Open SDLC"
        )

        panel.hover()
        page.wait_for_timeout(1000)

        logger.info("Opening panel menu")

        panel.locator(
            '[data-test-subj="embeddablePanelToggleMenuIcon"]'
        ).click()

        logger.info("Opening More menu")

        page.locator(
            '[data-test-subj="embeddablePanelMore-mainMenu"]'
        ).click()

        download_button = page.locator(
            '[data-test-subj="embeddablePanelAction-downloadCsvReport"]'
        )

        logger.info(
            f"Download button visible: {download_button.is_visible()}"
        )

        logger.info(
            f"Download button enabled: {download_button.is_enabled()}"
        )

        logger.info("Starting CSV download")

        download_start = time.time()

        with page.expect_download(timeout=7400000) as download_info:
            download_button.click()

        logger.info("Download event received")

        download = download_info.value

        logger.info(
            f"Suggested filename: {download.suggested_filename}"
        )

        try:
            failure = download.failure()

            if failure:
                logger.error(f"Download failure reported: {failure}")
            else:
                logger.info(
                    "Download object reports no immediate failure"
                )

        except Exception as failure_ex:
            logger.warning(
                f"Unable to check download failure state: {failure_ex}"
            )

        save_path = (
            fr"C:\Users\{USERNAME}\Downloads"
            fr"\APM Open Vulnerabilities_{todays_date}.csv"
        )

        logger.info(f"Saving file to: {save_path}")

        download.save_as(save_path)

        elapsed = round(time.time() - download_start, 2)

        logger.info(
            f"CSV successfully saved in {elapsed} seconds"
        )

        logger.info(f"Saved file: {save_path}")

        total_elapsed = round(time.time() - script_start, 2)

        logger.info(
            f"SCRIPT COMPLETED SUCCESSFULLY ({total_elapsed} seconds)"
        )

except Exception as e:

    logger.error("=" * 80)
    logger.error("SCRIPT FAILED")
    logger.error(str(e))
    logger.error(traceback.format_exc())

    try:

        if page:

            screenshot_path = (
                fr"C:\Users\{USERNAME}\Downloads\FIG_Open_Vulnerabilities"
                fr"\error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )

            page.screenshot(
                path=screenshot_path,
                full_page=True
            )

            logger.info(
                f"Failure screenshot saved: {screenshot_path}"
            )

    except Exception as screenshot_error:

        logger.error(
            f"Unable to save screenshot: {screenshot_error}"
        )

    raise

finally:

    try:

        if context:
            logger.info("Closing browser context")
            context.close()

        if browser:
            logger.info("Closing browser")
            browser.close()

    except Exception as cleanup_error:

        logger.warning(
            f"Cleanup warning: {cleanup_error}"
        )

    logger.info("SCRIPT ENDED")
