class ApiRequestError(Exception):
    """Пользовательское исключение для ошибок запросов к API."""
    def __init__(self, message="Ошибка API-запроса."):
        self.message = message
        super().__init__(self.message)


class MessageError(Exception):
    """Пользовательское исключение отправки сообщений."""
    def __init__(self, message="Ошибка отправки сообщения."):
        self.message = message
        super().__init__(self.message)