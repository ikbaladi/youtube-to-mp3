import uuid
from typing import Dict
from app.models import TaskStatus, TaskResponse
import asyncio


class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
    
    async def create_task(self, total_videos: int = 1) -> str:
        """Create a new task and return task_id"""
        task_id = str(uuid.uuid4())
        
        async with self._lock:
            self.tasks[task_id] = {
                "status": TaskStatus.PENDING,
                "progress": 0.0,
                "message": "Task created",
                "total_videos": total_videos,
                "completed_videos": 0,
                "file_paths": []
            }
        
        return task_id
    
    async def update_task(
        self, 
        task_id: str, 
        status: TaskStatus = None,
        progress: float = None,
        message: str = None,
        completed_videos: int = None,
        file_path: str = None
    ):
        """Update task status"""
        async with self._lock:
            if task_id not in self.tasks:
                return
            
            if status:
                self.tasks[task_id]["status"] = status
            if progress is not None:
                self.tasks[task_id]["progress"] = progress
            if message:
                self.tasks[task_id]["message"] = message
            if completed_videos is not None:
                self.tasks[task_id]["completed_videos"] = completed_videos
            if file_path:
                self.tasks[task_id]["file_paths"].append(file_path)
    
    async def get_task(self, task_id: str) -> TaskResponse:
        """Get task status"""
        async with self._lock:
            if task_id not in self.tasks:
                return TaskResponse(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    message="Task not found"
                )
            
            task = self.tasks[task_id]
            return TaskResponse(
                task_id=task_id,
                status=task["status"],
                message=task["message"],
                progress=task["progress"],
                total_videos=task["total_videos"],
                completed_videos=task["completed_videos"]
            )
    
    async def get_task_files(self, task_id: str) -> list:
        """Get downloaded file paths"""
        async with self._lock:
            if task_id not in self.tasks:
                return []
            return self.tasks[task_id].get("file_paths", [])
    
    async def cleanup_task(self, task_id: str):
        """Remove task from memory"""
        async with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]


# Global task manager instance
task_manager = TaskManager()