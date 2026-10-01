class CheckpointVerifier:

    def __init__(self, surface):
        self.surface = surface

    def verify(self, checkpoint) -> bool:
        checkpoint_type = checkpoint.type
        target = checkpoint.target.model_dump()

        if checkpoint_type in ("visible", "text"):
            return self._verify_visible(target)

        raise ValueError(
            f"Unsupported checkpoint type: {checkpoint_type}"
        )

    def _verify_visible(self, target) -> bool:
        strategy = target.get("strategy")

        try:
            if strategy =="id":
                locator = self.surface.page.locator(f"#{target['value']}")

            elif strategy == "text":
                locator = self.surface.page.get_by_text(
                    target.get("value")
                )

            elif strategy == "label":
                locator = self.surface.page.get_by_label(
                    target.get("name")
                )

            elif strategy == "role":
                locator = self.surface.page.get_by_role(
                    target.get("role"),
                    name=target.get("name")
                )

            else:
                raise ValueError(
                    f"Unsupported checkpoint strategy: {strategy}"
                )

            return locator.is_visible()

        except Exception:
            return False