from playwright.sync_api import sync_playwright

from app.browser.surface import Surface

from app.replay.errors import RecoverableReplayError

class PlaywrightSurface(Surface):

    def __init__(self, base_url="http://localhost:5173",fail_click_once=False):
        self.base_url = base_url
        self.fail_click_once = fail_click_once
        self.click_failed = False

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False
        )

        self.page = self.browser.new_page()

    def open(self):
        self.page.goto(self.base_url)

    def _get_locator(self, target):
        strategy = target.get("strategy")

        if strategy == "id":
            element_id = target.get("value")

            if not element_id:
                raise ValueError("ID target requires 'value'")

            return self.page.locator(f"#{element_id}")

        elif strategy == "label":
            name = target.get("name")

            if not name:
                raise ValueError("Label target requires 'name'")

            return self.page.get_by_label(name)

        elif strategy == "role":
            role = target.get("role")
            name = target.get("name")

            if not role:
                raise ValueError("Role target requires 'role'")

            if name:
                return self.page.get_by_role(
                    role,
                    name=name
                )

            return self.page.get_by_role(role)

        elif strategy == "text":
            value = target.get("value")

            if not value:
                raise ValueError("Text target requires 'value'")

            return self.page.get_by_text(value)

        else:
            raise ValueError(f"Unsupported locator strategy: {strategy}")

    def click(self, target):
        if self.fail_click_once and not self.click_failed:
            self.click_failed = True
            raise Exception("network error: temporarily unavailable")

        locator = self._get_locator(target)
        locator.click(timeout=5000)

    def navigate(self,url):
        self.page.goto(url)

    def fill(self, target, value):
        locator = self._get_locator(target)

        locator.fill(value)

        actual_value = locator.input_value()

        if actual_value != value:
            raise RuntimeError(
                f"Fill verification failed: "
                f"expected '{value}', got '{actual_value}'"
            )

    def extract(self, target):
        locator = self._get_locator(target)
        locator.wait_for(state="visible", timeout=5000)
        return locator.text_content()

    def screenshot(self, path):
        self.page.screenshot(path=path)

    def is_visible(self, target):
        locator = self._get_locator(target)
        return locator.is_visible()

    def wait_for_visible(self, target, timeout=2000):
        locator = self._get_locator(target)

        try:
            locator.wait_for(
                state="visible",
                timeout=timeout,
            )
            return True
        except Exception:
            return False
    def get_page_text(self):
        return self.page.locator("body").inner_text()

    def close(self):
        self.browser.close()
        self.playwright.stop()