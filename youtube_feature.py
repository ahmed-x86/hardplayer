# youtube_feature.py

"""
Facade Pattern:
This file aggregates functions and classes from the split files (infrastructure and dialogs)
so that you do not have to change anything in other project files like (main_window.py and others).
"""

# Import Backend files
from yt_url_parser import clean_ansi, clean_youtube_url
from yt_assets_fetcher import ImageFetcher
from yt_info_fetcher import YTInfoFetcher
from yt_downloader import DownloadWorker
from yt_search_engine import YTSearchEngine

# Import the new windows file (Dialogs)
from yt_dialogs import YouTubeSimpleQualityDialog, YouTubeQualityDialog, YouTubeSearchDialog

# Specify what will be exported directly to the rest of the project
__all__ = [
    "clean_ansi",
    "clean_youtube_url",
    "ImageFetcher",
    "YTInfoFetcher",
    "DownloadWorker",
    "YTSearchEngine",
    "YouTubeSimpleQualityDialog",
    "YouTubeQualityDialog",
    "YouTubeSearchDialog"
]