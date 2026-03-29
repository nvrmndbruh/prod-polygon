import json
import time
from pathlib import Path
from typing import Callable

import pylxd

from app.core.config import settings


class LXCService:
    BASE_IMAGE = "prod-polygon-base"
    COMPOSE_FILE_PATH = "/opt/environment/compose.yml"
    COMPOSE_WORKDIR = "/opt/environment"

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

    def _emit_progress(
        self,
        progress_callback: Callable[[str, str], None] | None,
        stage: str,
        message: str,
    ) -> None:
        if progress_callback is None:
            return
        try:
            progress_callback(stage, message)
        except Exception:
            pass

    def _wait_for_docker_daemon(
        self,
        container,
        timeout: int = 90,
        interval: float = 2.0,
    ) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                result = container.execute(["docker", "info"])
                if result.exit_code == 0:
                    return True
            except Exception:
                pass
            time.sleep(interval)
        return False

    def _run_compose_up_with_retry(
        self,
        container,
        max_attempts: int = 8,
        delay_seconds: int = 5,
    ):
        transient_markers = (
            "cannot connect to the docker daemon",
            "is the docker daemon running",
            "connect: connection refused",
            "dial unix",
            "context deadline exceeded",
            "error during connect",
        )

        last_result = None
        for attempt in range(1, max_attempts + 1):
            result = container.execute(
                [
                    "docker", "compose",
                    "-f", self.COMPOSE_FILE_PATH,
                    "up", "-d",
                ],
                cwd=self.COMPOSE_WORKDIR,
            )
            last_result = result

            if result.exit_code == 0:
                return result

            stderr = (result.stderr or "").lower()
            stdout = (result.stdout or "").lower()
            transient = any(mark in stderr or mark in stdout for mark in transient_markers)

            if not transient or attempt == max_attempts:
                break

            time.sleep(delay_seconds)

        return last_result

    def _parse_compose_rows(self, raw: str) -> list[dict]:
        text = (raw or "").strip()
        if not text:
            return []

        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [row for row in parsed if isinstance(row, dict)]
            if isinstance(parsed, dict):
                return [parsed]
        except Exception:
            pass

        rows = []
        for line in text.splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
            except Exception:
                continue
        return rows

    def _compose_service_names_from_file(self, container) -> list[str]:
        try:
            raw = container.files.get(self.COMPOSE_FILE_PATH)
            text = raw.decode("utf-8", errors="ignore") if isinstance(raw, (bytes, bytearray)) else str(raw)
        except Exception:
            return []

        service_names = []
        in_services_block = False
        services_indent = 0

        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue

            indent = len(line) - len(line.lstrip(" "))
            stripped = line.strip()

            if not in_services_block:
                if stripped == "services:":
                    in_services_block = True
                    services_indent = indent
                continue

            if indent <= services_indent:
                break

            if (
                indent == services_indent + 2
                and stripped.endswith(":")
                and not stripped.startswith("-")
            ):
                name = stripped[:-1].strip()
                if name:
                    service_names.append(name)

        return service_names

    def _count_running_services_by_name(self, container, service_names: list[str]) -> int:
        if not service_names:
            return 0

        try:
            result = container.execute([
                "docker", "ps", "-a", "--format", "{{.Names}}|||{{.Status}}",
            ])
            if result.exit_code != 0:
                return 0

            container_rows = []
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                parts = line.split("|||", 1)
                if len(parts) != 2:
                    continue
                container_rows.append((parts[0].strip(), parts[1].strip().lower()))

            running_services = 0
            for service_name in service_names:
                if any(
                    (f"-{service_name}-" in container_name or f"_{service_name}_" in container_name)
                    and "exited" not in status
                    and "dead" not in status
                    for container_name, status in container_rows
                ):
                    running_services += 1

            return running_services
        except Exception:
            return 0

    def _compose_service_counts(self, container) -> tuple[int, int]:
        try:
            service_names = self._compose_service_names_from_file(container)
            if service_names:
                total = len(service_names)
                running_by_names = self._count_running_services_by_name(container, service_names)

                running_res = container.execute(
                    [
                        "docker", "compose",
                        "-f", self.COMPOSE_FILE_PATH,
                        "ps", "--services", "--status", "running",
                    ],
                    cwd=self.COMPOSE_WORKDIR,
                )

                running_by_compose = 0
                if running_res.exit_code == 0:
                    running_service_names = {
                        line.strip() for line in running_res.stdout.splitlines() if line.strip()
                    }
                    running_by_compose = sum(
                        1 for service_name in service_names if service_name in running_service_names
                    )

                running = max(running_by_names, running_by_compose)
                return min(running, total), total

            configured_res = container.execute(
                [
                    "docker", "compose",
                    "-f", self.COMPOSE_FILE_PATH,
                    "config", "--services",
                ],
                cwd=self.COMPOSE_WORKDIR,
            )
            running_res = container.execute(
                [
                    "docker", "compose",
                    "-f", self.COMPOSE_FILE_PATH,
                    "ps", "--services", "--status", "running",
                ],
                cwd=self.COMPOSE_WORKDIR,
            )

            if configured_res.exit_code == 0 and running_res.exit_code == 0:
                configured_services = [
                    line.strip() for line in configured_res.stdout.splitlines() if line.strip()
                ]
                if configured_services:
                    running_services = [
                        line.strip() for line in running_res.stdout.splitlines() if line.strip()
                    ]
                    total = len(configured_services)
                    running = min(len(running_services), total)
                    return running, total

            result = container.execute(
                [
                    "docker", "compose",
                    "-f", self.COMPOSE_FILE_PATH,
                    "ps", "-a", "--format", "json",
                ],
                cwd=self.COMPOSE_WORKDIR,
            )
            if result.exit_code == 0:
                rows = self._parse_compose_rows(result.stdout)
                if rows:
                    total = len(rows)
                    running = 0
                    for row in rows:
                        state = str(row.get("State", "")).strip().lower()
                        status = str(row.get("Status", "")).strip().lower()
                        if state == "running" or (
                            status.startswith("up") and "restarting" not in status
                        ):
                            running += 1
                    return running, total

            total_res = container.execute(
                [
                    "docker", "compose",
                    "-f", self.COMPOSE_FILE_PATH,
                    "ps", "--services",
                ],
                cwd=self.COMPOSE_WORKDIR,
            )
            if total_res.exit_code != 0 or running_res.exit_code != 0:
                return 0, 0

            total = len([line for line in total_res.stdout.splitlines() if line.strip()])
            running = len([line for line in running_res.stdout.splitlines() if line.strip()])
            return running, total
        except Exception:
            return 0, 0

    def _status_is_running(self, status: str) -> bool:
        normalized = (status or "").strip().lower()
        if not normalized:
            return False
        if "restarting" in normalized or "exited" in normalized or "dead" in normalized:
            return False
        return "up" in normalized or "running" in normalized

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
        self,
        session_id: str,
        environment_path: str,
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> None:
        container_name = self._get_container_name(session_id)
        env_dir = self._get_environment_dir(environment_path)

        if not env_dir.exists():
            raise RuntimeError(
                f"Каталог окружения не найден: {env_dir}"
            )

        self._emit_progress(
            progress_callback,
            "lxd_starting",
            "Запуск LXD-контейнера...",
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

        self._emit_progress(
            progress_callback,
            "provisioning",
            "Подготовка файлов окружения...",
        )
        time.sleep(2)

        self._copy_directory_to_container(
            container, env_dir, "/opt/environment"
        )

        self._emit_progress(
            progress_callback,
            "compose_starting",
            "Запуск Docker-контейнеров...",
        )

        if not self._wait_for_docker_daemon(container, timeout=90):
            raise RuntimeError("Docker внутри LXD-контейнера не готов к запуску compose")

        result = self._run_compose_up_with_retry(container)

        if result.exit_code != 0:
            running_count, total_count = self._compose_service_counts(container)
            if total_count == 0:
                raise RuntimeError(
                    f"Не удалось запустить окружение: {result.stderr}"
                )

        self._emit_progress(
            progress_callback,
            "services_booting",
            "Контейнеры окружения запускаются...",
        )

    def get_session_status(self, session_id: str) -> dict:
        container_name = self._get_container_name(session_id)

        try:
            container = self.client.instances.get(container_name)
            container.sync()
        except pylxd.exceptions.LXDAPIException:
            return {
                "exists": False,
                "is_ready": False,
                "containers": [],
                "running_count": 0,
                "total_count": 0,
                "connections": [],
                "connections_ok": False,
                "lxd_status": "NotFound",
            }

        if container.status != "Running":
            return {
                "exists": True,
                "is_ready": False,
                "containers": [],
                "running_count": 0,
                "total_count": 0,
                "connections": [],
                "connections_ok": False,
                "lxd_status": container.status,
            }

        containers = self.get_containers(session_id)
        fallback_running = sum(
            1 for c in containers if self._status_is_running(c.get("status", ""))
        )
        running_count, total_count = self._compose_service_counts(container)

        if total_count == 0:
            total_count = len(containers)
            running_count = fallback_running
        else:
            running_count = max(running_count, min(fallback_running, total_count))

        connections = []
        connections_ok = False
        if total_count >= 3 and running_count == total_count:
            try:
                connections = self.check_connections(session_id)
                connections_ok = len(connections) > 0 and all(c.get("ok") for c in connections)
            except Exception:
                connections_ok = False

        is_ready = total_count >= 3 and running_count == total_count and connections_ok

        return {
            "exists": True,
            "is_ready": is_ready,
            "containers": containers,
            "running_count": running_count,
            "total_count": total_count,
            "connections": connections,
            "connections_ok": connections_ok,
            "lxd_status": container.status,
        }

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