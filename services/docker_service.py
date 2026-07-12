"""
services/docker_service.py
Collects Docker engine status: version, running/stopped containers,
image count, and volume count. Gracefully degrades when Docker is not
installed or the socket is unreachable (e.g. inside a restricted container).
"""

from typing import Any, Dict

from utils.logger import logger

try:
    import docker
    from docker.errors import DockerException

    DOCKER_SDK_AVAILABLE = True
except ImportError:  # pragma: no cover
    DOCKER_SDK_AVAILABLE = False


class DockerService:
    """Provides Docker engine metrics via the Docker SDK for Python."""

    def _get_client(self):
        if not DOCKER_SDK_AVAILABLE:
            return None
        try:
            return docker.from_env(timeout=2)
        except Exception:
            return None

    def get_docker_info(self) -> Dict[str, Any]:
        client = self._get_client()

        if client is None:
            return {
                "installed": False,
                "available": False,
                "version": None,
                "running_containers": 0,
                "stopped_containers": 0,
                "images_count": 0,
                "volumes_count": 0,
                "message": "Docker is not installed, not running, or the socket is unreachable.",
            }

        try:
            version_info = client.version()
            containers = client.containers.list(all=True)
            running = [c for c in containers if c.status == "running"]
            stopped = [c for c in containers if c.status != "running"]
            images = client.images.list()
            volumes = client.volumes.list()

            return {
                "installed": True,
                "available": True,
                "version": version_info.get("Version", "unknown"),
                "api_version": version_info.get("ApiVersion", "unknown"),
                "running_containers": len(running),
                "stopped_containers": len(stopped),
                "images_count": len(images),
                "volumes_count": len(volumes),
                "containers": [
                    {
                        "id": c.short_id,
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else c.image.short_id,
                    }
                    for c in containers[:20]
                ],
            }
        except Exception as exc:
            logger.warning("Docker daemon unreachable: %s", exc)
            return {
                "installed": True,
                "available": False,
                "version": None,
                "running_containers": 0,
                "stopped_containers": 0,
                "images_count": 0,
                "volumes_count": 0,
                "message": "Docker daemon is not reachable.",
            }
        finally:
            try:
                client.close()
            except Exception:
                pass


docker_service = DockerService()
