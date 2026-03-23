import time
from pathlib import Path

import pylxd

from app.core.config import settings


class LXCService:
    """
    Сервис управления пользовательскими окружениями через LXD API.
    Подключается к LXD через HTTPS используя клиентский сертификат.
    """

    BASE_IMAGE = "prod-polygon-base"

    def __init__(self):
        self._client = None

    @property
    def client(self) -> pylxd.Client:
        """Ленивое подключение к LXD API."""
        if self._client is None:
            self._client = pylxd.Client(
                endpoint=settings.LXD_URL,
                cert=(settings.LXD_CERT, settings.LXD_KEY),
                verify=False,
            )
        return self._client

    def _get_container_name(self, session_id: str) -> str:
        """Имя LXD-контейнера — короткое, без дефисов."""
        short_id = session_id.replace("-", "")[:16]
        return f"pp-{short_id}"

    def _get_environment_dir(self, environment_path: str) -> Path:
        """Путь до каталога окружения на хосте."""
        return Path(settings.ENVIRONMENTS_PATH) / environment_path

    def _copy_directory_to_container(
        self, container, src_dir: Path, dst_dir: str
    ) -> None:
        """
        Рекурсивно копирует каталог с хоста внутрь LXD-контейнера.
        """
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
        """
        Создаёт LXD-контейнер из базового образа и запускает окружение внутри.
        Копирует весь каталог окружения чтобы были доступны все файлы
        (compose.yml, nginx.conf и прочие конфиги).
        """
        container_name = self._get_container_name(session_id)
        env_dir = self._get_environment_dir(environment_path)

        if not env_dir.exists():
            raise RuntimeError(
                f"Каталог окружения не найден: {env_dir}"
            )

        # Создаём контейнер из базового образа с профилями для Docker
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

        # Ждём пока контейнер полностью запустится
        time.sleep(3)

        # Копируем весь каталог окружения внутрь контейнера
        self._copy_directory_to_container(
            container, env_dir, "/opt/environment"
        )

        # Запускаем docker compose внутри контейнера
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
        """Останавливает и удаляет LXD-контейнер."""
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

    def get_containers(self, session_id: str) -> list[dict]:
        """Список Docker-контейнеров внутри LXD-контейнера."""
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
        """Логи Docker-сервиса внутри LXD-контейнера."""
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

    def run_script(
        self, session_id: str, script_path: str
    ) -> tuple[int, str]:
        """Выполняет inject.sh или validate.sh внутри LXD-контейнера."""
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
        """Проверяет существование контейнера."""
        container_name = self._get_container_name(session_id)
        try:
            self.client.instances.get(container_name)
            return True
        except pylxd.exceptions.LXDAPIException:
            return False

    def get_container_websocket(self, session_id: str):
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
            }
        )

        data = response.json()
        operation_id = data["operation"].split("/")[-1]
        fds = data["metadata"]["metadata"]["fds"]
        
        secret = fds["0"]
        control_secret = fds.get("control", "")

        return operation_id, secret, control_secret


lxc_service = LXCService()