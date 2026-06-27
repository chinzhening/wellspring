from dagster import ConfigurableResource
from googleapiclient.discovery import build


class YoutubeResource(ConfigurableResource):
    api_key: str

    def client(self):
        return build("youtube", "v3", developerKey=self.api_key)
