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

APM_VALUES = ["APM0003145","APM0008659","APM0004316","APM0003424","APM0004383","APM0003659","APM0004288","APM0003782","APM0003334","APM0006087","APM0003234","APM0003119","APM0005271","APM0005525","APM0006014","APM0003646","APM0003655","APM0004455","APM0004453","APM0003624","APM0004192","APM0003606","APM0003375","APM0003324","APM0003750","APM0010996","APM0004335","APM0003254","APM0003062","APM0003620","APM0003278","APM0005526","APM0004609","APM0004226","APM0006543","APM0004169","APM0003405","APM0003944","APM0003134","APM0003660","APM0009637","APM0004216","APM0003231","APM0004671","APM0004436","APM0005334","APM0003760","APM0010997","APM0003690","APM0003758","APM0003052","APM0003121","APM0003416","APM0004161","APM0004233","APM0003421","APM0002880","APM0004668","APM0003064","APM0002815","APM0003153","APM0003611","APM0005529","APM0003610","APM0004289","APM0003096","APM0003057","APM0011140","APM0003154","APM0003522","APM0005173","APM0005531","APM0004149","APM0006020","APM0005255","APM0003926","APM0006561","APM0001057","APM0003687","APM0008563","APM0003344","APM0007340","APM0003427","APM0012042","APM0003752","APM0001310","APM0004249","APM0003945","APM0003292","APM0004171","APM0003842","APM0001696","APM0003249","APM0004014","APM0004220","APM0003295","APM0004305","APM0003807","APM0003434","APM0003365","APM0008381","APM0004450","APM0003961","APM0003159","APM0004222","APM0003138","APM0005530","APM0004336","APM0006802","APM0004164","APM0004206","APM0004488","APM0008286","APM0003061","APM0004238","APM0004150","APM0003058","APM0011997","APM0003753","APM0004176","APM0003631","APM0003473","APM0008495","APM0007108","APM0003526","APM0004261","APM0009579","APM0005272","APM0003384","APM0003735","APM0006565","APM0003322","APM0007618","APM0004431","APM0003089","APM0005532","APM0004203","APM0004158","APM0003255","APM0003499","APM0004132","APM0004633","APM0003382","APM0011584","APM0006676","APM0004323","APM0003733","APM0004141","APM0006572","APM0003723","APM0003845","APM0004193","APM0003739","APM0004820","APM0004046","APM0004327","APM0001041","APM0004458","APM0003621","APM0004293","APM0004370","APM0003934","APM0003460","APM0004136","APM0004269","APM0006618","APM0004432","APM0003056","APM0006988","APM0003439","APM0004292","APM0003261","APM0007417","APM0003651","APM0003455","APM0004186","APM0003190","APM0003218","APM0004191","APM0009160","APM0003925","APM0003835","APM0004168","APM0004277","APM0004421","APM0006466","APM0003615","APM0003592","APM0003370","APM0003220","APM0004443","APM0003625","APM0005682","APM0003180","APM0008615","APM0006559","APM0003326","APM0003846","APM0003146","APM0003429","APM0001053","APM0003353","APM0003263","APM0003212","APM0006488","APM0003962","APM0004437","APM0003188","APM0004274","APM0004310","APM0004195","APM0004217","APM0003251","APM0004239","APM0004225","APM0003116","APM0001855","APM0004139","APM0004170","APM0003488","APM0003253","APM0003585","APM0003644","APM0006267","APM0001710","APM0008924","APM0003765","APM0003256","APM0009580","APM0001511","APM0003352","APM0003219","APM0003230","APM0004445","APM0003675","APM0005476","APM0003184","APM0001052","APM0005270","APM0003085","APM0003616","APM0004184","APM0006962","APM0003441","APM0004287","APM0003282","APM0004051","APM0006933","APM0004214","APM0003216","APM0003260","APM0004308","APM0011993","APM0001027","APM0006019","APM0003178","APM0003413","APM0003617","APM0004414","APM0003197","APM0004467","APM0006888","APM0004306","APM0003432","APM0009255","APM0003593","APM0003605","APM0004777","APM0003081","APM0003884","APM0003490","APM0003608","APM0004199","APM0003308","APM0003137","APM0003451","APM0008237","APM0004205","APM0004202","APM0003858","APM0004055","APM0003367","APM0003368","APM0004208","APM0006831","APM0004419","APM0001044","APM0007610","APM0011316","APM0003649","APM0007181","APM0003454","APM0003692","APM0003225","APM0003348","APM0004430","APM0006467","APM0003369","APM0003736","APM0003204","APM0004401","APM0003351","APM0001040","APM0003250","APM0003126","APM0003629","APM0003270","APM0004181","APM0001026","APM0003740","APM0001046","APM0004159","APM0003053","APM0003142","APM0003350","APM0004244","APM0003247","APM0003166","APM0004474","APM0003955","APM0004133","APM0003100","APM0004299","APM0004433","APM0004236","APM0003338","APM0003435","APM0003688","APM0005591","APM0003686","APM0004281","APM0003339","APM0011327","APM0004201","APM0004282","APM0009835","APM0003127","APM0003757","APM0003362","APM0003602","APM0003055","APM0003181","APM0001043","APM0003599","APM0003164","APM0003280","APM0003633","APM0003294","APM0003183","APM0003407","APM0003415","APM0004047","APM0003174","APM0003281","APM0003202","APM0006091","APM0005430","APM0004219","APM0003177","APM0003458","APM0003400","APM0008765","APM0010861","APM0003492","APM0006024","APM0003684","APM0006463","APM0003115","APM0004138","APM0006608","APM0005164","APM0003410","APM0003236","APM0003325","APM0003657","APM0003113","APM0003636","APM0003414","APM0003640","APM0004200","APM0003647","APM0004329","APM0004963","APM0004218","APM0004481","APM0003478","APM0003277","APM0007230"]

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
            headless=True,
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
