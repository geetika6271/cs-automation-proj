class PageObserver:

    def __init__(self, page):
        self.page = page

    def observe(self):
        return {
            "url": self.page.url,
            "title": self.page.title(),
            "text": self.page.locator("body").inner_text(),
            "buttons": self._observe_buttons(),
            "inputs": self._observe_inputs(),
            "elements": self._observe_identifiable_elements(),
        }

    def _observe_buttons(self):
        buttons = self.page.locator("button").all()

        button_info = []

        for button in buttons:
            try:
                button_info.append({
                    "id": button.get_attribute("id"),
                    "text": button.inner_text().strip(),
                    "role": "button",
                    "aria_label": button.get_attribute("aria-label"),
                    "safety": button.get_attribute("data-safety"),
                })
            except Exception:
                pass

        return button_info

    def _observe_inputs(self):
        inputs = self.page.locator("input").all()

        input_info = []

        for input_element in inputs:
            try:
                input_info.append({
                    "id": input_element.get_attribute("id"),
                    "type": input_element.get_attribute("type"),
                    "name": input_element.get_attribute("name"),
                    "aria_label": input_element.get_attribute("aria-label"),
                    "placeholder": input_element.get_attribute("placeholder"),
                    "value": input_element.input_value(),
                })
            except Exception:
                pass

        return input_info

    def _observe_identifiable_elements(self):
        elements = self.page.locator(
            "[id], [aria-label]"
        ).all()

        element_info = []

        for element in elements:
            try:
                element_id = element.get_attribute("id")
                aria_label = element.get_attribute("aria-label")

                # Skip elements that don't have either
                # identifier.
                if not element_id and not aria_label:
                    continue

                text = ""

                try:
                    text = element.inner_text().strip()
                except Exception:
                    pass

                element_info.append({
                    "id": element_id,
                    "aria_label": aria_label,
                    "tag": element.evaluate( "(el) => el.tagName"),
                    "text": text,
                    "safety": element.get_attribute("data-safety"),
                })

            except Exception:
                pass

        return element_info