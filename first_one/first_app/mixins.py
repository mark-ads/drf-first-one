import logging

logger = logging.getLogger("first_app")


class LoggingMixin:
    """Миксин для логгирования POST, PUT, PATCH, DELETE операций для ViewSet."""

    def perform_create(self, serializer):
        username = self._get_username()

        try:
            instance = serializer.save()
            model_name, id, name = self._get_instance_info(instance)
            logger.info(
                f"Создан: {model_name}, id: {id}, название: {name}, пользователем {username}.",
            )
        except Exception as e:
            logger.error(f"Ошибка POST {e}")
            raise

    def perform_update(self, serializer):
        username = self._get_username()

        try:
            instance = serializer.save()
            model_name, id, name = self._get_instance_info(instance)
            logger.info(
                f"Изменён: {model_name}, id: {id}, название: {name}, пользователем {username}.",
            )
        except Exception as e:
            logger.error(f"Ошибка PUT {e}")
            raise

    def perform_destroy(self, instance):
        username = self._get_username()

        try:
            model_name, id, name = self._get_instance_info(instance)
            instance.delete()
            logger.info(
                f"Удалён: {model_name}, id: {id}, название: {name}, пользователем {username}.",
            )
        except Exception as e:
            logger.error(f"Ошибка DELETE {e}")
            raise

    def _get_username(self) -> str:
        '''Вернуть имя из запроса или "Не авторизован"'''
        try:
            request = getattr(self, "request")
            user = getattr(request, "user")
            username = getattr(user, "username", "Не авторизован")
            return username
        except AttributeError:
            return "Не авторизован"

    def _get_instance_info(self, instance) -> tuple[str, str, str]:
        """Вернуть тип и айди объекта"""
        try:
            id = getattr(instance, "id", "id неизвестен")
            model_meta = getattr(instance, "_meta", None)
            model_name = getattr(model_meta, "model_name", "Тип неизвестен")
            name = getattr(instance, "name", "Название неизвестно")
            return model_name, id, name
        except AttributeError:
            return "Тип неизвестен", "id неизвестен", "название неизвестно"
