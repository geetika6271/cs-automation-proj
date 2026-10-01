import json
from pathlib import Path
from app.artifiact.schema import Capability

class ArtifactStorage:

    def save(self,capability: Capability,directory: str = "artifacts",) -> str:

        output_dir = Path(directory)
        output_dir.mkdir(parents=True,exist_ok=True)

        path = output_dir / f"{capability.capability_id}.json"

        with path.open("w",encoding="utf-8") as file:

            json.dump(
                capability.model_dump(),
                file,
                indent=2,
                ensure_ascii=False,
            )

        return str(path)

    def load(self, path: str) -> Capability:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        return Capability.model_validate(data)