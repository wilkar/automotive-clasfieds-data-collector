import os
from distutils.util import strtobool  # type: ignore
from pathlib import Path


def env_bool(env_name: str, default_value: bool | None) -> bool:
    if env_name not in os.environ:
        if default_value is None:
            raise ValueError(f"Missing value for {env_name}")

        return default_value

    return bool(strtobool(os.environ[env_name]))


def env_enum(env_name: str, options: list[str], default_value: str | None) -> str:
    value = os.environ.get(env_name)

    if value is None and default_value is not None:
        return default_value

    if value not in options:
        raise ValueError(
            f"Invalid value for {env_name} environment variables, received {value}, possible options {', '.join(options)}"
        )

    return value


def env_path(env_name: str, default_value: Path | None) -> Path:
    if env_name not in os.environ:
        if default_value is None:
            raise ValueError(f"Missing value for {env_name}")

        return default_value

    return Path(os.environ[env_name])


def env_float(env_name: str, default_value: float | None) -> float:
    if env_name not in os.environ:
        if default_value is None:
            raise ValueError(f"Missing value for {env_name}")

        return default_value

    return float(os.environ[env_name])


def env_int(env_name: str, default_value: int | None) -> int:
    if env_name not in os.environ:
        if default_value is None:
            raise ValueError(f"Missing value for {env_name}")

        return default_value

    return int(os.environ[env_name])
