# youtube_feature.py

"""
واجهة التجميع (Facade Pattern):
هذا الملف يقوم بتجميع الدوال والأصناف من الملفات المقسمة (البنية التحتية والنوافذ)
حتى لا تضطر لتغيير أي شيء في ملفات المشروع الأخرى مثل (main_window.py وغيرها).
"""

# استدعاء ملفات الـ Backend
from yt_url_parser import clean_ansi, clean_youtube_url
from yt_assets_fetcher import ImageFetcher
from yt_info_fetcher import YTInfoFetcher
from yt_downloader import DownloadWorker
from yt_search_engine import YTSearchEngine

# استدعاء ملف النوافذ الجديد (Dialogs)
from yt_dialogs import YouTubeSimpleQualityDialog, YouTubeQualityDialog, YouTubeSearchDialog

# تحديد ما سيتم تصديره لباقي المشروع بشكل مباشر
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