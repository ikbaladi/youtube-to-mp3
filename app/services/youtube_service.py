import yt_dlp
import asyncio
from pathlib import Path
from typing import List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.models import VideoInfo, TaskStatus
from app.utils.helpers import sanitize_filename
from app.services.task_manager import task_manager

logger = logging.getLogger(__name__)


class YouTubeService:
    
    def __init__(self):
        self.download_dir = settings.DOWNLOAD_DIR
        self.executor = ThreadPoolExecutor(max_workers=1)
        
    def _get_base_ydl_opts(self):
        """Get base yt-dlp options with headers"""
        return {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
    def _get_ydl_opts(self, output_path: str, progress_callback=None):
        """Get yt-dlp options for download"""
        opts = self._get_base_ydl_opts()
        opts.update({
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': settings.AUDIO_FORMAT,
                'preferredquality': str(settings.AUDIO_QUALITY),
            }],
        })
        
        if progress_callback:
            opts['progress_hooks'] = [progress_callback]
        
        return opts
    
    async def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """Get single video information"""
        try:
            ydl_opts = self._get_base_ydl_opts()
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
                return VideoInfo(
                    id=info['id'],
                    title=info['title'],
                    duration=info.get('duration', 0),
                    thumbnail=info.get('thumbnail', ''),
                    selected=True
                )
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None
    
    async def get_playlist_info(self, url: str) -> tuple[Optional[str], List[VideoInfo]]:
        """Get playlist information"""
        try:
            ydl_opts = self._get_base_ydl_opts()
            ydl_opts['extract_flat'] = True
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
                if 'entries' not in info:
                    return None, []
                
                playlist_title = info.get('title', 'Playlist')
                videos = []
                
                for entry in info['entries']:
                    if entry:
                        videos.append(VideoInfo(
                            id=entry['id'],
                            title=entry['title'],
                            duration=entry.get('duration', 0),
                            thumbnail=entry.get('thumbnail', ''),
                            selected=True
                        ))
                
                return playlist_title, videos
        except Exception as e:
            logger.error(f"Error getting playlist info: {e}")
            return None, []
    
    async def download_single_video(self, url: str, task_id: str):
        """Download and convert single video"""
        try:
            await task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                message="Fetching video information...",
                progress=10.0
            )
            
            # Get video info first
            video_info = await self.get_video_info(url)
            if not video_info:
                await task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message="Failed to fetch video information"
                )
                return
            
            filename = sanitize_filename(video_info.title)
            output_path = str(self.download_dir / f"{filename}.%(ext)s")
            
            # Get event loop reference for the hook
            loop = asyncio.get_running_loop()
            last_percent = [0]  # Use list to maintain reference
            
            # Progress hook that safely schedules async updates
            def progress_hook(d):
                try:
                    if d['status'] == 'downloading':
                        percent_str = d.get('_percent_str', '0%').strip('%')
                        try:
                            percent = float(percent_str)
                            # Only update if change is significant (every 5%)
                            if abs(percent - last_percent[0]) >= 5:
                                last_percent[0] = percent
                                # Schedule coroutine in the main event loop
                                asyncio.run_coroutine_threadsafe(
                                    task_manager.update_task(
                                        task_id,
                                        progress=10 + (percent * 0.7),
                                        message=f"Downloading: {percent:.0f}%"
                                    ),
                                    loop
                                )
                        except (ValueError, TypeError):
                            pass
                    elif d['status'] == 'finished':
                        asyncio.run_coroutine_threadsafe(
                            task_manager.update_task(
                                task_id,
                                progress=80.0,
                                message="Converting to MP3..."
                            ),
                            loop
                        )
                except Exception as e:
                    logger.error(f"Progress hook error: {e}")
            
            ydl_opts = self._get_ydl_opts(output_path, progress_hook)
            
            # Download and convert
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                await asyncio.to_thread(ydl.download, [url])
            
            # Wait a bit for file to be fully written
            await asyncio.sleep(0.5)
            

            # Find the converted file
            final_file = self.download_dir / f"{filename}.{settings.AUDIO_FORMAT}"

            # Tambahkan logging
            logger.info(f"Looking for file: {final_file}")
            logger.info(f"File exists: {final_file.exists()}")

            if final_file.exists():
                logger.info(f"File size: {final_file.stat().st_size} bytes")
                await task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    progress=100.0,
                    message="Download completed!",
                    completed_videos=1,
                    file_path=str(final_file)
                )
            else:
                logger.error(f"File not found after conversion: {final_file}")
                await task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message="File conversion failed"
                )
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            await task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                message=f"Error: {str(e)}"
            )
    
    async def download_playlist(self, video_ids: List[str], task_id: str):
        """Download multiple videos from playlist"""
        try:
            total = len(video_ids)
            completed = 0
            
            await task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                message=f"Starting download of {total} videos..."
            )
            
            for idx, video_id in enumerate(video_ids):
                try:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    video_info = await self.get_video_info(url)
                    
                    if not video_info:
                        logger.warning(f"Skipping video {video_id}")
                        continue
                    
                    filename = sanitize_filename(video_info.title)
                    output_path = str(self.download_dir / f"{filename}.%(ext)s")
                    
                    await task_manager.update_task(
                        task_id,
                        message=f"Downloading {idx + 1}/{total}: {video_info.title[:50]}..."
                    )
                    
                    ydl_opts = self._get_ydl_opts(output_path)
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        await asyncio.to_thread(ydl.download, [url])
                    
                    # Wait for file to be fully written
                    await asyncio.sleep(0.5)
                    
                    final_file = self.download_dir / f"{filename}.{settings.AUDIO_FORMAT}"
                    
                    if final_file.exists():
                        completed += 1
                        progress = (completed / total) * 100
                        
                        await task_manager.update_task(
                            task_id,
                            progress=progress,
                            completed_videos=completed,
                            file_path=str(final_file)
                        )
                
                except Exception as e:
                    logger.error(f"Error downloading {video_id}: {e}")
                    continue
            
            if completed > 0:
                await task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message=f"Completed! Downloaded {completed}/{total} videos",
                    progress=100.0
                )
            else:
                await task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message="No videos were downloaded successfully"
                )
                
        except Exception as e:
            logger.error(f"Playlist download error: {e}")
            await task_manager.update_task(
                task_id,
                status=TaskStatus.FAILED,
                message=f"Error: {str(e)}"
            )


# Global service instance
youtube_service = YouTubeService()