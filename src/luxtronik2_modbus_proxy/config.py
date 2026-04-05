"""Configuration module for luxtronik2-modbus-proxy.

Loads proxy configuration from a YAML file with environment variable overrides.
All environment variables use the LUXTRONIK_ prefix (e.g., LUXTRONIK_POLL_INTERVAL=60).

Configuration precedence (highest to lowest):
1. Environment variables (LUXTRONIK_*)
2. YAML config file
3. Field defaults
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, YamlConfigSettingsSource


class RegistersConfig(BaseModel):
    """User-selectable extra parameters beyond curated defaults.

    Parameters are specified by their Luxtronik symbolic name (e.g., 'ID_Einst_WK_akt').
    The proxy resolves names to Luxtronik indices at startup and exposes them
    as additional holding registers.

    Attributes:
        parameters: List of Luxtronik parameter names to expose as extra holding registers.
    """

    parameters: list[str] = Field(
        default_factory=list,
        description="Extra Luxtronik parameter names to expose as holding registers",
    )


class ProxyConfig(BaseSettings):
    """Configuration for the Luxtronik 2.0 to Modbus TCP proxy.

    Loaded from a YAML file with environment variable overrides.
    The YAML file path defaults to 'config.yaml' in the working directory.
    Override by setting the yaml_file entry in model_config or by using load_config().

    Attributes:
        luxtronik_host: Hostname or IP address of the Luxtronik 2.0 controller.
        luxtronik_port: TCP port of the Luxtronik binary protocol server.
        modbus_port: TCP port to expose the Modbus TCP server on.
        bind_address: Network interface to bind the Modbus TCP server to.
        poll_interval: How often (in seconds) to poll the Luxtronik controller.
        log_level: Logging verbosity level (DEBUG, INFO, WARNING, ERROR).
        enable_writes: Whether to allow Modbus write commands to reach the controller.
        write_rate_limit: Minimum seconds between writes to the same register.
    """

    model_config: ClassVar[Any] = {
        "yaml_file": "config.yaml",
        "env_prefix": "LUXTRONIK_",
        "extra": "ignore",
    }

    luxtronik_host: str = Field(
        description="Hostname or IP address of the Luxtronik 2.0 controller (port 8889)"
    )
    luxtronik_port: int = Field(
        default=8889,
        description="TCP port of the Luxtronik binary protocol server",
    )
    modbus_port: int = Field(
        default=502,
        description="TCP port to expose the Modbus TCP server on",
    )
    bind_address: str = Field(
        default="0.0.0.0",
        description="Network interface to bind the Modbus server to",
    )
    poll_interval: int = Field(
        default=30,
        ge=10,
        description="Polling interval in seconds (min 10) — lower values increase Luxtronik load",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging verbosity level: DEBUG, INFO, WARNING, or ERROR",
    )
    enable_writes: bool = Field(
        default=False,
        description="Allow Modbus write commands to reach the Luxtronik controller (safety default: off)",
    )
    write_rate_limit: int = Field(
        default=60,
        ge=10,
        description="Minimum seconds between writes to the same register (protects NAND flash)",
    )
    registers: RegistersConfig = Field(
        default_factory=RegistersConfig,
        description="Extra registers to expose beyond curated defaults",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Customize settings source priority order.

        Priority: init kwargs > environment variables > YAML file > defaults.
        Environment variables use LUXTRONIK_ prefix (e.g., LUXTRONIK_POLL_INTERVAL).
        This allows Docker deployments to override YAML config via env vars.

        Args:
            settings_cls: The settings class being configured.
            init_settings: Settings from __init__ keyword arguments.
            env_settings: Settings from environment variables.
            dotenv_settings: Settings from .env file (not used).
            file_secret_settings: Settings from secret files (not used).

        Returns:
            Tuple of sources in priority order (first = highest priority).
        """
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(settings_cls),
        )


def load_config(yaml_path: str | None = None) -> ProxyConfig:
    """Load proxy configuration from a YAML file with environment variable overrides.

    Creates a ProxyConfig subclass dynamically when a custom yaml_path is provided,
    so the YamlConfigSettingsSource reads from the specified file.

    Args:
        yaml_path: Optional path to the YAML configuration file. If not provided,
            uses the default 'config.yaml' in the working directory.

    Returns:
        Validated ProxyConfig instance.

    Raises:
        pydantic.ValidationError: If the configuration is invalid.
    """
    if yaml_path is None:
        return ProxyConfig()

    # Dynamically create a subclass with the overridden yaml_file path.
    # pydantic-settings reads yaml_file from model_config at class level,
    # so we must create a new class (not instance) to override the path.
    overridden_config: Any = {
        "yaml_file": yaml_path,
        "env_prefix": "LUXTRONIK_",
        "extra": "ignore",
    }

    class _PathOverrideConfig(ProxyConfig):
        model_config: ClassVar[Any] = overridden_config

    return _PathOverrideConfig()
