class ApiRequestError(Exception):
    """Пользовательское исключение для ошибок запросов к API."""
    def __init__(self, message="Ошибка API-запроса."):
        self.message = message
        super().__init__(self.message)
        

class ApiJsonError(Exception):
    """Пользовательское исключение для ошибок запросов к API."""
    def __init__(self, message="API-ответ не JSON."):
        self.message = message
        super().__init__(self.message)

class IsinstanceError(TypeError):
    """Пользовательское исключение отправки сообщений."""
    def __init__(self, message="Ошибка типа ответа."):
        self.message = message
        super().__init__(self.message)


class MessageError(Exception):
    """Пользовательское исключение отправки сообщений."""
    def __init__(self, message="Ошибка отправки сообщения."):
        self.message = message
        super().__init__(self.message)


class ValueKeyError(ValueError):
    """Пользовательское исключение отправки сообщений."""
    def __init__(self, message="Ошибка отправки сообщения."):
        self.message = message
        super().__init__(self.message)


