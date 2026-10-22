import httpx
from config.settings import settings
from typing import Optional, Dict, Any, List


class APIClient:
    """Client for API requests"""

    def __init__(self):
        self.base_url = f"http://{settings.api_host}:{settings.api_port}"

    async def create_project(
        self, owner_id: int, title: str, preset: str = "tiktok"
    ) -> Dict[str, Any]:
        """Create a new project"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/projects/",
                json={"owner_id": owner_id, "title": title, "preset": preset},
            )
            response.raise_for_status()
            return response.json()

    async def list_projects(self, owner_id: int) -> list:
        """List all projects for a user"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/projects/", params={"owner_id": owner_id}
            )
            response.raise_for_status()
            return response.json()

    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """Get a project by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/projects/{project_id}")
            response.raise_for_status()
            return response.json()

    async def update_project(self, project_id: int, **kwargs) -> Dict[str, Any]:
        """Update a project"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/projects/{project_id}", json=kwargs
            )
            response.raise_for_status()
            return response.json()

    async def delete_project(self, project_id: int):
        """Delete a project"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/projects/{project_id}")
            response.raise_for_status()
            return response.json()

    async def create_asset(
        self, project_id: int, alias: str, filename: str, path: str, duration: float
    ) -> Dict[str, Any]:
        """Create a new asset"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/assets/",
                json={
                    "project_id": project_id,
                    "alias": alias,
                    "filename": filename,
                    "path": path,
                    "duration": duration,
                },
            )
            response.raise_for_status()
            return response.json()

    async def list_assets(self, project_id: int) -> list:
        """List all assets for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/assets/project/{project_id}")
            response.raise_for_status()
            return response.json()

    async def delete_asset(self, asset_id: int):
        """Delete an asset"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/assets/{asset_id}")
            response.raise_for_status()
            return response.json()

    async def create_segment(
        self,
        project_id: int,
        asset_alias: str,
        in_sec: float,
        out_sec: float,
        order: int,
    ) -> Dict[str, Any]:
        """Create a new segment"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/timeline/",
                json={
                    "project_id": project_id,
                    "asset_alias": asset_alias,
                    "in_sec": in_sec,
                    "out_sec": out_sec,
                    "order": order,
                },
            )
            response.raise_for_status()
            return response.json()

    async def list_segments(self, project_id: int) -> List[Dict[str, Any]]:
        """List all segments for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/timeline/project/{project_id}"
            )
            response.raise_for_status()
            return response.json()

    async def get_segment(self, segment_id: int) -> Dict[str, Any]:
        """Get a segment by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/timeline/{segment_id}")
            response.raise_for_status()
            return response.json()

    async def delete_segment(self, segment_id: int):
        """Delete a segment"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/timeline/{segment_id}")
            response.raise_for_status()
            return response.json()

    async def move_segment(self, segment_id: int, new_order: int) -> Dict[str, Any]:
        """Move a segment to a new position"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/timeline/{segment_id}/move",
                json={"new_order": new_order},
            )
            response.raise_for_status()
            return response.json()

    async def update_segment(self, segment_id: int, **kwargs) -> Dict[str, Any]:
        """Update a segment"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/timeline/{segment_id}", json=kwargs
            )
            response.raise_for_status()
            return response.json()

    async def create_subtitle(
        self, project_id: int, start_sec: float, end_sec: float, text: str
    ) -> Dict[str, Any]:
        """Create a new subtitle"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/subtitles/",
                json={
                    "project_id": project_id,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "text": text,
                },
            )
            response.raise_for_status()
            return response.json()

    async def list_subtitles(self, project_id: int) -> List[Dict[str, Any]]:
        """List all subtitles for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/subtitles/project/{project_id}"
            )
            response.raise_for_status()
            return response.json()

    async def get_subtitle(self, subtitle_id: int) -> Dict[str, Any]:
        """Get a subtitle by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/subtitles/{subtitle_id}")
            response.raise_for_status()
            return response.json()

    async def delete_subtitle(self, subtitle_id: int):
        """Delete a subtitle"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/subtitles/{subtitle_id}")
            response.raise_for_status()
            return response.json()

    async def create_bgm(
        self, project_id: int, filename: str, path: str, volume: float = 0.25
    ) -> Dict[str, Any]:
        """Create or update BGM"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/audio/bgm",
                json={
                    "project_id": project_id,
                    "filename": filename,
                    "path": path,
                    "volume": volume,
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_bgm(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get BGM for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/audio/bgm/project/{project_id}"
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def update_bgm(self, bgm_id: int, volume: float) -> Dict[str, Any]:
        """Update BGM volume"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/audio/bgm/{bgm_id}", json={"volume": volume}
            )
            response.raise_for_status()
            return response.json()

    async def delete_bgm(self, bgm_id: int):
        """Delete BGM"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/audio/bgm/{bgm_id}")
            response.raise_for_status()
            return response.json()

    async def create_sfx(
        self,
        project_id: int,
        filename: str,
        path: str,
        at_sec: float,
        volume: float = 0.6,
    ) -> Dict[str, Any]:
        """Create a new SFX"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/audio/sfx",
                json={
                    "project_id": project_id,
                    "filename": filename,
                    "path": path,
                    "at_sec": at_sec,
                    "volume": volume,
                },
            )
            response.raise_for_status()
            return response.json()

    async def list_sfx(self, project_id: int) -> List[Dict[str, Any]]:
        """List all SFX for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/audio/sfx/project/{project_id}"
            )
            response.raise_for_status()
            return response.json()

    async def delete_sfx(self, sfx_id: int):
        """Delete an SFX"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/audio/sfx/{sfx_id}")
            response.raise_for_status()
            return response.json()

    async def start_render(self, project_id: int) -> Dict[str, Any]:
        """Start render for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/render/", json={"project_id": project_id}
            )
            response.raise_for_status()
            return response.json()

    async def get_render_status(self, project_id: int) -> Dict[str, Any]:
        """Get render status for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/render/status/{project_id}")
            response.raise_for_status()
            return response.json()

    async def clone_project(self, project_id: int) -> Dict[str, Any]:
        """Clone a project"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/projects/{project_id}/clone")
            response.raise_for_status()
            return response.json()

    async def list_overlays(self, project_id: int) -> List[Dict[str, Any]]:
        """List all overlays for a project"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/overlays/project/{project_id}"
            )
            response.raise_for_status()
            return response.json()

    async def create_overlay(self, project_id: int, **kwargs) -> Dict[str, Any]:
        """Create a new overlay"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/overlays/", json={"project_id": project_id, **kwargs}
            )
            response.raise_for_status()
            return response.json()

    async def get_overlay(self, overlay_id: int) -> Dict[str, Any]:
        """Get an overlay by ID"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/overlays/{overlay_id}")
            response.raise_for_status()
            return response.json()

    async def delete_overlay(self, overlay_id: int):
        """Delete an overlay"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/overlays/{overlay_id}")
            response.raise_for_status()
            return response.json()


api_client = APIClient()
