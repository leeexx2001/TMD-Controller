"""依赖注入容器模块

提供单例模式的依赖注入容器，支持服务注册、工厂函数和延迟初始化。
"""

from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, cast

if TYPE_CHECKING:
    import logging

    from .config.config import TMDConfig
    from .services.database_service import DatabaseService
    from .services.timestamp_service import TimestampService
    from .ui.ui_helper import UIHelper


class Container:
    """依赖注入容器

    实现单例模式，提供服务注册和解析功能。
    支持直接实例注册和工厂函数注册。
    """

    _instance: Optional["Container"] = None
    _instances: Dict[str, Any]
    _factories: Dict[str, Callable[[], Any]]
    _resolving: set

    def __new__(cls) -> "Container":
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._instances = {}
            cls._instance._factories = {}
            cls._instance._resolving = set()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "Container":
        """获取单例实例"""
        return cls()

    @classmethod
    def reset(cls) -> None:
        """重置单例实例"""
        if cls._instance is not None:
            cls._instance.clear()
            cls._instance = None

    @property
    def config(self) -> "TMDConfig":
        """获取配置实例"""
        from .config.config import TMDConfig

        return self.resolve("config") if self.has("config") else TMDConfig()

    @property
    def logger(self) -> "logging.Logger":
        """获取日志实例"""
        import logging

        if self.has("logger"):
            return cast("logging.Logger", self.resolve("logger"))
        return logging.getLogger("TMD")

    @property
    def database_service(self) -> "DatabaseService":
        """获取数据库服务实例"""
        from .services.database_service import DatabaseService

        if self.has("database_service"):
            return cast("DatabaseService", self.resolve("database_service"))
        return DatabaseService(self.config, self.logger)

    @property
    def timestamp_service(self) -> "TimestampService":
        """获取时间戳服务实例"""
        from .services.timestamp_service import TimestampService

        if self.has("timestamp_service"):
            return cast("TimestampService", self.resolve("timestamp_service"))
        download_service = self.resolve("download_service") if self.has("download_service") else None
        return TimestampService(self.config, self.logger, self.database_service, download_service)

    @property
    def ui(self) -> "UIHelper":
        """获取 UI 辅助实例"""
        from .ui.ui_helper import UIHelper

        if self.has("ui"):
            return cast("UIHelper", self.resolve("ui"))
        return UIHelper()

    def register(self, name: str, instance: Any) -> None:
        """注册服务实例"""
        self._instances[name] = instance

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """注册服务工厂"""
        self._factories[name] = factory

    def resolve(self, name: str) -> Any:
        """解析服务实例"""
        if name in self._resolving:
            raise RuntimeError(f"Circular dependency detected for service '{name}'")

        if name in self._instances:
            return self._instances[name]

        if name in self._factories:
            self._resolving.add(name)
            try:
                instance = self._factories[name]()
                self._instances[name] = instance
                return instance
            finally:
                self._resolving.discard(name)

        raise KeyError(f"Service '{name}' not registered")

    def has(self, name: str) -> bool:
        """检查服务是否已注册"""
        return name in self._instances or name in self._factories

    def clear(self) -> None:
        """清除所有已注册的服务"""
        self._instances.clear()
        self._factories.clear()
        self._resolving.clear()


__all__ = ["Container"]
