"""异常类型"""


class AlterBrowserError(Exception):
    """alterbrowser 基础异常"""


class BinaryNotFoundError(AlterBrowserError):
    """chrome.exe 二进制找不到"""


class ProfileLoadError(AlterBrowserError):
    """JSON profile 加载失败"""


class ProfileValidationError(AlterBrowserError):
    """Profile 字段值非法"""


class LaunchTimeoutError(AlterBrowserError):
    """启动超时 / 进程未存活"""


class IPAdaptError(AlterBrowserError):
    """IP 自适应查询失败（所有端点不可达）"""


class InconsistencyWarning(UserWarning):
    """指纹字段不一致警告（非致命）"""
