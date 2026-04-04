# -*- coding: utf-8 -*-
"""测试 container.py"""

import pytest
from tmdc.container import Container, get_service


class TestContainer:
    """容器测试"""

    def setup_method(self):
        """每个测试前重置容器"""
        Container.reset()

    def test_singleton_pattern(self):
        """测试单例模式"""
        c1 = Container()
        c2 = Container()
        assert c1 is c2

    def test_get_instance(self):
        """测试获取实例"""
        c1 = Container.get_instance()
        c2 = Container.get_instance()
        assert c1 is c2

    def test_register_and_resolve(self):
        """测试注册和解析"""
        container = Container.get_instance()
        container.register("test_service", {"key": "value"})
        result = container.resolve("test_service")
        assert result == {"key": "value"}

    def test_register_factory(self):
        """测试工厂注册"""
        container = Container.get_instance()
        call_count = [0]

        def factory():
            call_count[0] += 1
            return {"count": call_count[0]}

        container.register_factory("factory_service", factory)

        result1 = container.resolve("factory_service")
        assert result1 == {"count": 1}

        result2 = container.resolve("factory_service")
        assert result2 == {"count": 1}

    def test_resolve_not_found(self):
        """测试解析未注册服务"""
        container = Container.get_instance()
        with pytest.raises(KeyError):
            container.resolve("non_existent")

    def test_has_service(self):
        """测试检查服务是否存在"""
        container = Container.get_instance()
        assert not container.has("test")

        container.register("test", "value")
        assert container.has("test")

    def test_clear(self):
        """测试清除服务"""
        container = Container.get_instance()
        container.register("test", "value")
        assert container.has("test")

        container.clear()
        assert not container.has("test")

    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        container = Container.get_instance()

        def factory_a():
            return container.resolve("b")

        def factory_b():
            return container.resolve("a")

        container.register_factory("a", factory_a)
        container.register_factory("b", factory_b)

        with pytest.raises(RuntimeError, match="Circular dependency"):
            container.resolve("a")

    def test_get_service_helper(self):
        """测试便捷函数"""
        container = Container.get_instance()
        container.register("helper_test", "value")
        result = get_service("helper_test")
        assert result == "value"
