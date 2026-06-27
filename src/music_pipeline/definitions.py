from dagster import Definitions, load_assets_from_modules

from .assets import (
    analytics,
    catalog,
    export,
    indexing,
    lyrics,
    matching,
    normalization,
    serving,
    spotify,
    terms,
    website,
    youtube,
)
from .resources import gemini_resource, youtube_resource

assets = load_assets_from_modules(
    [
        analytics,
        catalog,
        export,
        indexing,
        lyrics,
        matching,
        website,
        youtube,
        serving,
        spotify,
        terms,
        normalization,
    ]
)

defs = Definitions(
    assets=[*assets],
    resources={"gemini": gemini_resource, "youtube": youtube_resource},
)
