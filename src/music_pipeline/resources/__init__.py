from dagster import EnvVar

from music_pipeline.resources.gemini import GeminiResource
from music_pipeline.resources.youtube import YoutubeResource

gemini_resource = GeminiResource(api_key=EnvVar("GEMINI_API_KEY"))
youtube_resource = YoutubeResource(api_key=EnvVar("YOUTUBE_API_KEY"))
