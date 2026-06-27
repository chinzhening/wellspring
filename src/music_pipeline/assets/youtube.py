from dagster import MaterializeResult, MetadataValue, asset, get_dagster_logger

from music_pipeline.resources.youtube import YoutubeResource


@asset(group_name="seeds")
def youtube_channel_ids() -> dict[str, str]:
    return {
        "SOP": "UC00EceQGGCMucNvwOS-jQ7A",
        "SOP Kids": "UC2KCkfsRUglpjc8tRM65DtQ",
    }


@asset(
    group_name="ingestion",
)
def youtube_videos_raw(
    youtube: YoutubeResource, youtube_channel_ids: dict[str, str]
) -> MaterializeResult:
    log = get_dagster_logger()
    client = youtube.client()

    all_videos = []

    for channel_name, channel_id in youtube_channel_ids.items():
        log.info(f"Fetching YouTube data for channel {channel_name}")

        # 1. get uploads playlist
        channel = (
            client.channels()
            .list(part="contentDetails", id=channel_id)
            .execute()["items"][0]
        )

        uploads_playlist_id = channel["contentDetails"]["relatedPlaylists"][
            "uploads"
        ]

        # 2. collect video IDs
        video_ids = []
        next_page = None

        while True:
            resp = (
                client.playlistItems()
                .list(
                    part="snippet",
                    playlistId=uploads_playlist_id,
                    maxResults=50,
                    pageToken=next_page,
                )
                .execute()
            )

            for item in resp["items"]:
                video_ids.append(item["snippet"]["resourceId"]["videoId"])

            next_page = resp.get("nextPageToken")
            if not next_page:
                break

        # 3. fetch video details
        videos = []

        for i in range(0, len(video_ids), 50):
            batch = video_ids[i : i + 50]

            res = (
                client.videos()
                .list(part="statistics,snippet", id=",".join(batch))
                .execute()
            )

            for item in res["items"]:
                videos.append(
                    {
                        "id": item["id"],
                        "published_at": item["snippet"]["publishedAt"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "views": int(item["statistics"].get("viewCount", 0)),
                        "url": f"https://www.youtube.com/watch?v={item['id']}",
                    }
                )

        all_videos.extend(videos)

    return MaterializeResult(
        value=all_videos,
        metadata={
            "num_records": len(all_videos),
            "samples": MetadataValue.json(all_videos[:3] if all_videos else {}),
        },
    )
