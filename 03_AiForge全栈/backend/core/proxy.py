import os
import requests
from config import OIIOII_API


class OiioiiProxy:
    def __init__(self, base_url: str = OIIOII_API):
        self.base = base_url.rstrip("/")

    def get_models(self) -> dict:
        try:
            r = requests.get(f"{self.base}/api/models", timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[OiioiiProxy] get_models error: {e}")
        return {}

    def generate_image(self, prompt: str, model: str, ratio: str = "1:1",
                       resolution: str = "1K", reference_images: list = None) -> dict:
        body = {"prompt": prompt, "model": model, "ratio": ratio, "resolution": resolution}
        if reference_images:
            body["reference_images"] = reference_images
        try:
            r = requests.post(f"{self.base}/api/generate_image", json=body, timeout=60)
            if r.status_code == 200:
                return r.json()
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def generate_video(self, prompt: str, model: str, ratio: str = "16:9",
                       resolution: str = "720p", duration: int = 5,
                       reference_images: list = None, reference_video: str = "",
                       camera_movement: str = "", reference_map: dict = None) -> dict:
        body = {
            "prompt": prompt, "model": model, "ratio": ratio,
            "resolution": resolution, "duration": duration,
        }
        if reference_images:
            body["reference_images"] = reference_images
        if reference_video:
            body["reference_video"] = reference_video
        if camera_movement:
            body["camera_movement"] = camera_movement
        if reference_map:
            body["reference_map"] = reference_map
        try:
            r = requests.post(f"{self.base}/api/generate_video", json=body, timeout=60)
            if r.status_code == 200:
                return r.json()
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def describe_image(self, image_url: str) -> dict:
        """Reverse prompt from image - uses oiioii's describe_image MCP method via video_generate endpoint."""
        body = {
            "prompt": image_url,
            "model": "describe_image",
            "ratio": "1:1",
            "resolution": "1K",
            "duration": 5,
            "reference_images": [image_url],
        }
        try:
            r = requests.post(f"{self.base}/api/generate_video", json=body, timeout=60)
            if r.status_code == 200:
                return r.json()
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def get_task(self, task_id: int) -> dict:
        try:
            r = requests.get(f"{self.base}/api/task/{task_id}", timeout=30)
            if r.status_code == 200:
                return r.json()
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def upload_ref(self, file_data: bytes, filename: str) -> dict:
        try:
            r = requests.post(
                f"{self.base}/api/upload_ref",
                files={"file": (filename, file_data)},
                timeout=120,
            )
            if r.status_code == 200:
                data = r.json()
                if "url" in data and data["url"].startswith("/output/refs/"):
                    data["url"] = data["url"].replace("/output/refs/", "/api/gen/refs/")
                return data
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

    def upload_video_ref(self, file_data: bytes, filename: str) -> dict:
        try:
            ext = os.path.splitext(filename)[1].lower()
            mime_map = {".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime", ".avi": "video/x-msvideo"}
            content_type = mime_map.get(ext, "video/mp4")
            r = requests.post(
                f"{self.base}/api/upload_video_ref",
                files={"file": (filename, file_data, content_type)},
                timeout=180,
            )
            if r.status_code == 200:
                data = r.json()
                if "uri" in data and data["uri"].startswith("/output/refs/"):
                    data["uri"] = data["uri"].replace("/output/refs/", "/api/gen/refs/")
                return data
            return {"error": f"HTTP {r.status_code}: {r.text[:300]}"}
        except Exception as e:
            return {"error": str(e)}
