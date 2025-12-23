from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import zipfile
from pathlib import Path
import logging
import asyncio

from app.models import (
    DownloadRequest, 
    PlaylistRequest, 
    TaskResponse,
    VideoInfoResponse
)
from app.services.youtube_service import youtube_service
from app.services.task_manager import task_manager
from app.utils.validators import is_valid_youtube_url

logger = logging.getLogger(__name__)
router = APIRouter()


async def cleanup_file(file_path: Path, delay: int = 30):
    """Delete file after delay"""
    await asyncio.sleep(delay)
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"✓ Cleaned up file: {file_path.name}")
        else:
            logger.warning(f"File already deleted: {file_path.name}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path.name}: {e}")


@router.post("/api/info", response_model=VideoInfoResponse)
async def get_video_info(request: DownloadRequest):
    """Get video or playlist information"""
    url = str(request.url)
    
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    # Check if playlist
    if "list=" in url:
        playlist_title, videos = await youtube_service.get_playlist_info(url)
        
        if not videos:
            raise HTTPException(status_code=404, detail="Playlist not found or empty")
        
        return VideoInfoResponse(
            is_playlist=True,
            videos=videos,
            playlist_title=playlist_title
        )
    else:
        video = await youtube_service.get_video_info(url)
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return VideoInfoResponse(
            is_playlist=False,
            videos=[video]
        )


@router.post("/api/download", response_model=TaskResponse)
async def download_video(
    request: DownloadRequest, 
    background_tasks: BackgroundTasks
):
    """Download single video"""
    url = str(request.url)
    
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    # Create task
    task_id = await task_manager.create_task(total_videos=1)
    
    # Start download in background
    background_tasks.add_task(
        youtube_service.download_single_video,
        url,
        task_id
    )
    
    return await task_manager.get_task(task_id)


@router.post("/api/download-playlist", response_model=TaskResponse)
async def download_playlist(
    request: PlaylistRequest,
    background_tasks: BackgroundTasks
):
    """Download selected videos from playlist"""
    if not request.video_ids:
        raise HTTPException(status_code=400, detail="No videos selected")
    
    # Create task
    task_id = await task_manager.create_task(total_videos=len(request.video_ids))
    
    # Start download in background
    background_tasks.add_task(
        youtube_service.download_playlist,
        request.video_ids,
        task_id
    )
    
    return await task_manager.get_task(task_id)


@router.get("/api/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """Get task status"""
    return await task_manager.get_task(task_id)

@router.get("/api/download-single/{task_id}/{file_index}")
async def download_single_from_playlist(
    task_id: str, 
    file_index: int,
    background_tasks: BackgroundTasks
):
    """Download single file from playlist"""
    task = await task_manager.get_task(task_id)
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    files = await task_manager.get_task_files(task_id)
    
    if not files or file_index >= len(files):
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(files[file_index])
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Sanitize filename
    safe_filename = file_path.name.encode('ascii', 'ignore').decode('ascii')
    if not safe_filename:
        safe_filename = f"audio_{file_index}.mp3"
    
    # Schedule cleanup after all files downloaded (longer delay for playlist)
    background_tasks.add_task(cleanup_file, file_path, 30)
    
    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type='audio/mpeg'
    )


@router.get("/api/download-file/{task_id}")
async def download_file(task_id: str, background_tasks: BackgroundTasks):
    """Download completed file(s) and auto-cleanup"""
    task = await task_manager.get_task(task_id)
    
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")
    
    files = await task_manager.get_task_files(task_id)
    
    if not files:
        raise HTTPException(status_code=404, detail="No files found")
    
    # Single file - direct download
    if len(files) == 1:
        file_path = Path(files[0])
        
        # Double check file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise HTTPException(status_code=404, detail=f"File not found: {file_path.name}")
        
        # Get file size
        file_size = file_path.stat().st_size
        logger.info(f"Sending file: {file_path.name} ({file_size} bytes)")
        
        # Sanitize filename untuk header (remove non-ASCII)
        safe_filename = file_path.name.encode('ascii', 'ignore').decode('ascii')
        if not safe_filename:
            safe_filename = f"audio_{task_id}.mp3"
        
        # Create response
        response = FileResponse(
            path=str(file_path),
            filename=safe_filename,
            media_type='audio/mpeg'
        )
        
        # Schedule cleanup after file is sent (10 seconds delay)
        background_tasks.add_task(cleanup_file, file_path, 10)
        
        return response
    
    # Multiple files - Return HTML page with download links
    else:
        from fastapi.responses import HTMLResponse
        
        # Generate download links
        html_content = f"""
        <!DOCTYPE html>
        <html lang="id">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Download MP3 Files</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-purple-600 to-blue-600 min-h-screen py-10 px-4">
            <div class="max-w-3xl mx-auto">
                <div class="bg-white rounded-2xl shadow-2xl p-8">
                    <h1 class="text-3xl font-bold text-gray-800 mb-6">📥 Download {len(files)} File MP3</h1>
                    <p class="text-gray-600 mb-6">Klik tombol dibawah untuk download satu per satu</p>
                    
                    <div class="space-y-3" id="downloadList">
        """
        
        for idx, file_path in enumerate(files, 1):
            path = Path(file_path)
            if path.exists():
                safe_name = path.name.encode('ascii', 'ignore').decode('ascii')
                if not safe_name:
                    safe_name = f"audio_{idx}.mp3"
                
                html_content += f"""
                    <div class="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                        <div class="flex-1 min-w-0">
                            <p class="font-medium text-gray-800 truncate">{idx}. {path.stem}</p>
                            <p class="text-sm text-gray-500">{path.suffix.upper()} • {path.stat().st_size // 1024} KB</p>
                        </div>
                        <a href="/api/download-single/{task_id}/{idx-1}" 
                           class="ml-4 px-6 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition">
                            Download
                        </a>
                    </div>
                """
        
        html_content += """
                    </div>
                    
                    <div class="mt-8 pt-6 border-t">
                        <button onclick="downloadAll()" class="w-full px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-lg transition">
                            ⬇️ Download Semua (Otomatis)
                        </button>
                        <a href="/" class="block mt-4 text-center text-gray-600 hover:text-gray-800">
                            ← Kembali ke Home
                        </a>
                    </div>
                </div>
            </div>
            
            <script>
                let currentIndex = 0;
                const totalFiles = """ + str(len(files)) + """;
                
                function downloadAll() {
                    if (currentIndex >= totalFiles) {
                        currentIndex = 0;
                        alert('Semua file selesai didownload!');
                        return;
                    }
                    
                    // Create hidden iframe for download
                    const iframe = document.createElement('iframe');
                    iframe.style.display = 'none';
                    iframe.src = `/api/download-single/""" + task_id + """/${currentIndex}`;
                    document.body.appendChild(iframe);
                    
                    currentIndex++;
                    
                    // Download next file after 2 seconds
                    if (currentIndex < totalFiles) {
                        setTimeout(downloadAll, 2000);
                    } else {
                        setTimeout(() => {
                            alert('Semua file selesai didownload!');
                            currentIndex = 0;
                        }, 2000);
                    }
                }
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)