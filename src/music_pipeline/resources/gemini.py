from dagster import ConfigurableResource
from google.genai import Client


class GeminiResource(ConfigurableResource):
    api_key: str

    def client(self) -> Client:
        return Client(api_key=self.api_key)
