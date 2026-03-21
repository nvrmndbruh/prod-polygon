import subprocess
from pathlib import Path

import docker
from docker.errors import NotFound

from app.core.config import settings


# сервис для управления Docker-окружениями
class DockerService:
    
    def __init__(self):
        self.client = docker.from_env()

    # уникальное имя проекта для изоляции контейнеров сессии
    def _get_project_name(self, session_id: str) -> str:
        return f"prodpolygon-{session_id}"

    # формирует абсолютный путь до compose.yml
    def _get_compose_path(self, environment_path: str) -> str:
        return str(
            Path(settings.ENVIRONMENTS_PATH) / environment_path / "compose.yml"
        )

    # запуск окружения
    def start_environment(self, session_id: str, environment_path: str) -> None:
        compose_path = self._get_compose_path(environment_path)
        project_name = self._get_project_name(session_id)

        result = subprocess.run(
            [
                "docker", "compose",
                "-p", project_name,
                "-f", compose_path,
                "up", "-d", "--build",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Не удалось запустить окружение: {result.stderr}"
            )

    # остановка и удаление окружения
    def stop_environment(self, session_id: str, environment_path: str) -> None:
        compose_path = self._get_compose_path(environment_path)
        project_name = self._get_project_name(session_id)

        result = subprocess.run(
            [
                "docker", "compose",
                "-p", project_name,
                "-f", compose_path,
                "down", "--remove-orphans",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Не удалось остановить окружение: {result.stderr}"
            )

    # получение списка контейнеров сессии
    def get_containers(self, session_id: str) -> list[dict]:
        project_name = self._get_project_name(session_id)
        containers = self.client.containers.list(
            all=True,
            filters={"label": f"com.docker.compose.project={project_name}"},
        )

        return [
            {
                "name": c.labels.get(
                    "com.docker.compose.service", c.name
                ),
                "status": c.status,
                "image": c.image.tags[0] if c.image.tags else "unknown",
            }
            for c in containers
        ]

    # получение логов контейнера
    def get_logs(
        self, session_id: str, service_name: str, lines: int = 100
    ) -> str:
        project_name = self._get_project_name(session_id)
        containers = self.client.containers.list(
            all=True,
            filters={
                "label": [
                    f"com.docker.compose.project={project_name}",
                    f"com.docker.compose.service={service_name}",
                ]
            },
        )

        if not containers:
            raise RuntimeError(
                f"Контейнер сервиса '{service_name}' не найден"
            )

        container = containers[0]
        logs = container.logs(tail=lines, timestamps=True).decode("utf-8")
        return logs

    # выполнение скрипта внутри контейнера
    def run_script(
        self, session_id: str, service_name: str, script_path: str
    ) -> tuple[int, str]:
        project_name = self._get_project_name(session_id)
        containers = self.client.containers.list(
            filters={
                "label": [
                    f"com.docker.compose.project={project_name}",
                    f"com.docker.compose.service={service_name}",
                ]
            }
        )

        if not containers:
            raise RuntimeError(
                f"Контейнер сервиса '{service_name}' не найден"
            )

        container = containers[0]
        exit_code, output = container.exec_run(
            f"sh {script_path}", demux=False
        )
        return exit_code, output.decode("utf-8") if output else ""

    # выполнение произвольной команды внутри контейнера (для терминала)
    def exec_command(
        self, session_id: str, service_name: str, command: str
    ) -> tuple[int, str]:
        project_name = self._get_project_name(session_id)
        containers = self.client.containers.list(
            filters={
                "label": [
                    f"com.docker.compose.project={project_name}",
                    f"com.docker.compose.service={service_name}",
                ]
            }
        )

        if not containers:
            raise RuntimeError(
                f"Контейнер сервиса '{service_name}' не найден"
            )

        container = containers[0]
        exit_code, output = container.exec_run(
            f"sh -c '{command}'", demux=False
        )
        return exit_code, output.decode("utf-8") if output else ""


docker_service = DockerService()