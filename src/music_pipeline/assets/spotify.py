from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from playwright.async_api import async_playwright


@asset(group_name="seeds")
def spotify_artist_ids() -> dict[str, str]:
    return {
        "SOP": "4doyJAIKxTGN2II0QpgUjT",
    }


@asset(group_name="ingestion")
async def spotify_songs_raw(
    context: AssetExecutionContext, spotify_artist_ids: dict[str, str]
) -> MaterializeResult:
    output = []

    async with async_playwright() as pw:
        browser = await get_browser(pw)
        page = await browser.new_page()

        for _, artist_id in spotify_artist_ids.items():
            output += await _scrape_tracks(context, page, artist_id)

    return MaterializeResult(
        value=output,
        metadata={
            "num_entries": len(output),
            "num_columns": len(output[0]) if output else 0,
            "samples": MetadataValue.json(output[:5]),
        },
    )


async def get_browser(pw):
    return await pw.chromium.launch(
        channel="chrome",
        args=[
            "--incognito",
            "--disable-blink-features=AutomationControlled",
        ],
        headless=False,
        slow_mo=100,
    )


async def _scrape_tracks(context, page, artist_id) -> list[dict[str, dict]]:
    seen = set()
    rows = {}
    handler = _make_response_handler(context, seen=seen, rows=rows)

    page.on("response", handler)
    await page.goto(
        f"https://open.spotify.com/artist/{artist_id}/discography/all"
    )
    await _scroll_page(context, page, rows)
    page.remove_listener("response", handler)

    return list(rows.values())


def _make_response_handler(
    context: AssetExecutionContext,
    seen: set[str],
    rows: dict[str, dict],
):
    async def handler(response):
        if "api-partner.spotify.com/pathfinder/v2/query" not in response.url:
            return

        data = await _parse_response(context, response)
        if data is None:
            return

        extracted = _extract(context, data, response)
        if extracted is None:
            return

        album_name, items = extracted

        try:
            for item in items:
                row = _build_row(context, item.get("track", {}), album_name)
                if row is None:
                    continue

                track_id, track_data = row
                if track_id in seen:
                    continue

                seen.add(track_id)
                rows[track_id] = track_data
        except Exception:
            context.log.error(
                "Error processing Spotify response: %s", response.url
            )

    return handler


async def _parse_response(
    context: AssetExecutionContext, response
) -> dict | None:
    try:
        return await response.json()
    except Exception:
        context.log.error(
            "Failed to parse JSON from Spotify response: %s", response.url
        )
        return None


def _extract(
    context: AssetExecutionContext, data: dict, response
) -> tuple[str, list[dict]] | None:
    try:
        album = data.get("data", {}).get("albumUnion", {})
        return album.get("name", ""), album.get("tracksV2", {}).get("items", [])
    except Exception:
        context.log.error(
            "Unexpected Spotify API payload shape: %s", response.url
        )
        try:
            context.log.debug(
                "Spotify response payload: %s", response.text()[:1000]
            )
        except Exception:
            pass
        return None


def _build_row(
    context: AssetExecutionContext, track: dict, album_name: str
) -> tuple[str, dict] | None:
    uri = track.get("uri", "")
    if not uri:
        return None

    track_id = uri.split(":")[-1]

    return track_id, {
        "track_id": track_id,
        "track_name": track.get("name", ""),
        "album_name": album_name,
        "track_number": track.get("trackNumber", 0),
        "duration_ms": track.get("duration", {}).get("totalMilliseconds", 0),
        "playcount": track.get("playcount"),
    }


async def _scroll_page(
    context: AssetExecutionContext, page, rows: dict[str, dict]
) -> None:
    """Scroll the main view until no new tracks arrive."""
    main_view = page.locator("#main-view")
    await main_view.wait_for(state="visible", timeout=5000)
    await main_view.scroll_into_view_if_needed()
    await main_view.hover()

    prev_count = 0
    while True:
        await page.wait_for_timeout(500)
        await page.mouse.wheel(0, 3000)

        if len(rows) == prev_count:
            break

        prev_count = len(rows)
