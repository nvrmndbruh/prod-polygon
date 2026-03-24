import time
from pathlib import Path

import pylxd

from app.core.config import settings


class LXCService:
    BASE_IMAGE = "prod-polygon-base"

    def __init__(self):
        self._client = None

    @property
    def client(self) -> pylxd.Client:
        if self._client is None:
            self._client = pylxd.Client(
                endpoint=settings.LXD_URL,
                cert=(settings.LXD_CERT, settings.LXD_KEY),
                verify=False,
            )
        return self._client

    def _get_container_name(self, session_id: str) -> str:
        short_id = session_id.replace("-", "")[:16]
        return f"pp-{short_id}"

    def _get_environment_dir(self, environment_path: str) -> Path:
        return Path(settings.ENVIRONMENTS_PATH) / environment_path

    def _copy_directory_to_container(
        self, container, src_dir: Path, dst_dir: str
    ) -> None:
        container.execute(["mkdir", "-p", dst_dir])

        for item in src_dir.rglob("*"):
            relative = item.relative_to(src_dir)

            if item.is_dir():
                container.execute(["mkdir", "-p", f"{dst_dir}/{relative}"])
            else:
                with open(item, "rb") as f:
                    container.files.put(
                        f"{dst_dir}/{relative}",
                        f.read(),
                    )

    def start_environment(
        self, session_id: str, environment_path: str
    ) -> None:
        container_name = self._get_container_name(session_id)
        env_dir = self._get_environment_dir(environment_path)

        if not env_dir.exists():
            raise RuntimeError(
                f"Каталог окружения не найден: {env_dir}"
            )

        container = self.client.instances.create(
            {
                "name": container_name,
                "source": {
                    "type": "image",
                    "alias": self.BASE_IMAGE,
                },
                "profiles": ["default", "docker-enabled"],
                "type": "container",
            },
            wait=True,
        )

        container.start(wait=True)
        time.sleep(3)

        self._copy_directory_to_container(
            container, env_dir, "/opt/environment"
        )

        result = container.execute(
            [
                "docker", "compose",
                "-f", "/opt/environment/compose.yml",
                "up", "-d",
            ],
            cwd="/opt/environment",
        )

        if result.exit_code != 0:
            raise RuntimeError(
                f"Не удалось запустить окружение: {result.stderr}"
            )

    def stop_environment(self, session_id: str) -> None:
        container_name = self._get_container_name(session_id)

        try:
            container = self.client.instances.get(container_name)

            container.execute([
                "docker", "compose",
                "-f", "/opt/environment/compose.yml",
                "down",
            ])

            container.stop(wait=True)
            container.delete(wait=True)
        except pylxd.exceptions.LXDAPIException:
            pass

    def restart_environment(self, session_id: str) -> None:
        container_name = self._get_container_name(session_id)

        try:
            container = self.client.instances.get(container_name)
        except pylxd.exceptions.LXDAPIException:
            raise RuntimeError("Контейнер не найден")

        container.execute([
            "docker", "compose",
            "-f", "/opt/environment/compose.yml",
            "down",
        ])

        result = container.execute([
            "docker", "compose",
            "-f", "/opt/environment/compose.yml",
            "up", "-d",
        ])

        if result.exit_code != 0:
            raise RuntimeError(
                f"Не удалось перезапустить окружение: {result.stderr}"
            )

    def get_containers(self, session_id: str) -> list[dict]:
        container_name = self._get_container_name(session_id)

        try:
            container = self.client.instances.get(container_name)
            result = container.execute([
                "docker", "ps", "-a",
                "--format", "{{.Names}}|||{{.Status}}|||{{.Image}}",
            ])

            containers = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|||")
                if len(parts) == 3:
                    full_name = parts[0]
                    name_parts = full_name.split("-")
                    service_name = name_parts[-2] if len(name_parts) >= 2 else full_name
                    containers.append({
                        "name": service_name,
                        "full_name": full_name,
                        "status": parts[1],
                        "image": parts[2],
                    })

            return containers
        except Exception:
            return []

    def get_logs(
        self, session_id: str, service_name: str, lines: int = 100
    ) -> str:
        container_name = self._get_container_name(session_id)

        try:
            container = self.client.instances.get(container_name)
            result = container.execute([
                "docker", "compose",
                "-f", "/opt/environment/compose.yml",
                "logs", f"--tail={lines}", service_name,
            ])
            return result.stdout
        except Exception as e:
            raise RuntimeError(str(e))

    def check_connections(self, session_id: str) -> list[dict]:
        container_name = self._get_container_name(session_id)

        try:
            container = self.client.instances.get(container_name)
        except pylxd.exceptions.LXDAPIException:
            return []

        results = []

        # backend → db и backend → redis через health эндпоинт
        health_check = container.execute([
            "docker", "exec", "environment-backend-1",
            "python3", "-c",
            "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/health', timeout=3).read().decode())",
        ])

        health_output = health_check.stdout if health_check.exit_code == 0 else ""

        db_ok = '"db":"ok"' in health_output
        redis_ok = '"redis":"ok"' in health_output

        results.append({"from": "backend", "to": "db", "ok": db_ok})
        results.append({"from": "backend", "to": "redis", "ok": redis_ok})

        # nginx → backend: проверяем через python из backend контейнера
        # обращаемся к nginx по имени сервиса внутри docker сети
        nginx_check = container.execute([
            "docker", "exec", "environment-backend-1",
            "python3", "-c",
            "import urllib.request; urllib.request.urlopen('http://nginx:80/health', timeout=3); print('ok')",
        ])

        results.append({
            "from": "nginx",
            "to": "backend",
            "ok": nginx_check.exit_code == 0,
        })

        return results

    def run_script(
        self, session_id: str, script_path: str
    ) -> tuple[int, str]:
        container_name = self._get_container_name(session_id)
        full_path = Path(settings.ENVIRONMENTS_PATH) / script_path

        if not full_path.exists():
            raise RuntimeError(f"Скрипт не найден: {full_path}")

        container = self.client.instances.get(container_name)

        with open(full_path, "rb") as f:
            container.files.put("/tmp/script.sh", f.read())

        container.execute(["chmod", "+x", "/tmp/script.sh"])
        result = container.execute(["bash", "/tmp/script.sh"])
        return result.exit_code, result.stdout + result.stderr

    def container_exists(self, session_id: str) -> bool:
        container_name = self._get_container_name(session_id)
        try:
            self.client.instances.get(container_name)
            return True
        except pylxd.exceptions.LXDAPIException:
            return False

    def get_container_websocket(
        self, session_id: str, cols: int = 80, rows: int = 24
    ):
        container_name = self._get_container_name(session_id)

        response = self.client.api.instances[container_name].exec.post(
            json={
                "command": ["/bin/bash", "--login"],
                "environment": {
                    "TERM": "xterm-256color",
                    "LANG": "en_US.UTF-8",
                },
                "wait-for-websocket": True,
                "interactive": True,
                "width": cols,
                "height": rows,
            }
        )

        data = response.json()
        operation_id = data["operation"].split("/")[-1]
        fds = data["metadata"]["metadata"]["fds"]
        secret = fds["0"]
        control_secret = fds.get("control", "")

        return operation_id, secret, control_secret


lxc_service = LXCService()