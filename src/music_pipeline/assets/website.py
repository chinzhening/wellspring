from dagster import MaterializeResult, MetadataValue, asset
from playwright.async_api import async_playwright


@asset(group_name="seeds")
def sop_url() -> str:
    return "https://sop.org/songs/"


@asset(group_name="ingestion")
async def sop_songs_raw(sop_url: str) -> MaterializeResult:
    output = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(sop_url)

        table = await _get_table(page)
        headers = await _get_headers(table)

        while True:
            for row in await _get_rows(table):
                output.append(await _extract_row_data(row, headers))

            next_btn = await page.query_selector("button.dt-paging-button.next")
            if next_btn is None or await _is_next_disabled(next_btn):
                break

            await next_btn.click()
            await page.wait_for_timeout(50)

        await browser.close()
    return MaterializeResult(
        value=output,
        metadata={
            "num_entries": len(output),
            "num_columns": len(output[0]) if output else 0,
            "samples": MetadataValue.json(output[:3]),
        },
    )


# Helper Functions


async def _get_table(page):
    await page.wait_for_selector("table#tablepress-3")
    table = await page.query_selector("table#tablepress-3")
    if table is None:
        raise RuntimeError(
            "Could not find SOP songs table with id 'tablepress-3'"
        )
    return table


async def _get_headers(table) -> list[str]:
    headers = await table.query_selector_all("thead tr th")
    if not headers:
        raise RuntimeError("Could not find table headers in thead tr th")
    return [await h.inner_text() for h in headers]


async def _get_rows(table):
    rows = await table.query_selector_all("tbody tr")
    if not rows:
        raise RuntimeError("Could not find any rows in the table body")
    return rows


async def _extract_row_data(row, headers: list[str]) -> dict:
    HEADER_MAP = {
        "曲名": "title",
        "作曲": "composer",
        "作詞": "lyricist",
        "專輯名稱": "album",
        "專輯系列": "series",
        "調性": "key",
        "歌詞": "lyrics",
    }
    cells = await row.query_selector_all("td")
    return {
        f"raw_{HEADER_MAP[headers[i]]}": await _extract_cell_data(cells[i])
        for i in range(len(cells))
    }


async def _extract_cell_data(cell) -> str:
    return await cell.inner_html()


async def _is_next_disabled(btn) -> bool:
    disabled = (
        await btn.get_attribute("aria-disabled")
        or await btn.get_attribute("tabindex") == "-1"
        or (
            (cls := await btn.get_attribute("class")) is not None
            and "disabled" in cls.split()
        )
    )
    return disabled == "true"
