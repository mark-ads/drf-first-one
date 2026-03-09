from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from first_one.first_app.models import Event, EventPlace


class BaseApiTest(TestCase):
    """Базовый класс для тестирования АПИ.

    Создает суперпользователя, пользователя, место, ивент.
    Имеет методы для создания формы нового ивента, авторизации пользователя и админа.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="admin_test", email="admin@admin.test", password="admin_test"
        )

        self.user = User.objects.create_user(
            username="user_test", email="user@user.test", password="user_test"
        )

        self.place = EventPlace.objects.create(
            name="Тестовое место", latitude=1.5, longitude=1.5
        )

        self.draft_event = Event.objects.create(
            name="Тестовый черновик мероприятие",
            description="Описание тестового черновика мероприятия",
            publish_date=datetime.now() + timedelta(days=1),
            start_date=datetime.now() + timedelta(days=2),
            end_date=datetime.now() + timedelta(days=3),
            author=self.admin,
            place=self.place,
            rating=15,
            status=Event.StatusChoices.DRAFT,
        )

        self.published_event = Event.objects.create(
            name="Тестовое опубликованное мероприятие",
            description="Описание тестового опубликованного мероприятия",
            publish_date=datetime.now(),
            start_date=datetime.now() + timedelta(days=1),
            end_date=datetime.now() + timedelta(days=2),
            author=self.admin,
            place=self.place,
            rating=15,
            status=Event.StatusChoices.PUBLISHED,
        )

        self.started_event = Event.objects.create(
            name="Тестовое начавшееся мероприятие",
            description="Описание тестового начавшегося мероприятия",
            publish_date=datetime.now() - timedelta(days=1),
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=2),
            author=self.admin,
            place=self.place,
            rating=15,
            status=Event.StatusChoices.STARTED,
        )

        self.ended_event = Event.objects.create(
            name="Тестовое завершившееся мероприятие",
            description="Описание тестового завершившегося мероприятия",
            publish_date=datetime.now() - timedelta(days=2),
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            author=self.admin,
            place=self.place,
            rating=15,
            status=Event.StatusChoices.ENDED,
        )

    def get_new_event_data(
        self, user
    ) -> dict[
        str, str | float | int | datetime | User | EventPlace | Event.StatusChoices
    ]:
        """Вернуть готовую форму для создания нового мероприятя."""
        data = {
            "name": "Тестовое создающееся мероприятие",
            "description": "Описание тестового создающего мероприятия",
            "publish_date": datetime.now(),
            "start_date": datetime.now() + timedelta(days=1),
            "end_date": datetime.now() + timedelta(days=2),
            "author": user.id,
            "place": self.place.id,  # type: ignore
            "rating": 15,
            "status": Event.StatusChoices.PUBLISHED,
        }
        return data

    def authenticate_admin(self):
        """Залогинить суперпользователя."""
        self.client.force_login(user=self.admin)

    def authenticate_user(self):
        """Залогинить обычного пользователя."""
        self.client.force_login(user=self.user)


class EventViewTest(BaseApiTest):
    """Тесты для EventViewSet."""

    def test_event_list_unauthorized(self):
        """Тест GET запроса от неавторизованного пользователя.

        Шаги:
            1. Отправить GET в /api/events/.
            2. Проверить, что ответ 403.
        """
        url = reverse("event-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)

    def test_event_list_user(self):
        """Тест GET запроса от авторизованного пользователя.

        Шаги:
            1. Авторизовать обычного пользователя.
            2. Отправить GET в /api/events/.
            3. Проверить, что ответ 200.
            4. Проверить, что статусы только Опубликовано и Начавшееся.
        """
        self.authenticate_user()
        url = reverse("event-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        for e in response.data["results"]:  # type: ignore
            self.assertIn(e["status"], ["published", "started"])

    def test_event_list_admin(self):
        """Тест GET запроса от суперпользователя.

        Шаги:
            1. Авторизовать суперпользователя.
            2. Отправить GET в /api/events/.
            3. Проверить, что ответ 200.
            4. Проверить, что статусы все возможные.
        """
        self.authenticate_admin()
        url = reverse("event-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        for e in response.data["results"]:  # type: ignore
            self.assertIn(e["status"], ["draft", "published", "started", "ended"])

    def test_event_create_user(self):
        """Тест POST запроса от обычного пользователя.

        Шаги:
            1. Авторизовать пользователя.
            2. Отправить POST в /api/events/.
            3. Проверить, что ответ 403.
        """
        self.authenticate_user()
        url = reverse("event-list")
        data = self.get_new_event_data(self.user)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_event_create_admin(self):
        """Тест POST запроса от суперпользователя.

        Шаги:
            1. Авторизовать суперпользователя.
            2. Получить форму для создания мероприятия.
            3. Отправить POST в /api/events/.
            4. Проверить, что ответ 201.
            5. Проверить, что автор и название мероприятия правильные.
        """
        self.authenticate_admin()
        url = reverse("event-list")
        data = self.get_new_event_data(self.admin)
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["author_info"]["username"], self.admin.username)  # type: ignore
        self.assertEqual(response.data["name"], data["name"])  # type: ignore

    def test_event_update_user(self):
        """Тест PUT запроса от обычного пользователя.

        Шаги:
            1. Авторизовать пользователя.
            2. Получить форму для создания мероприятия.
            3. Отправить PUT в /api/events/{published_event.id}.
            4. Проверить, что ответ 403.
        """
        self.authenticate_user()
        url = reverse("event-detail", kwargs={"pk": self.published_event.id})  # type: ignore
        data = self.get_new_event_data(self.user)
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_event_update_admin(self):
        """Тест PUT запроса от суперпользователя.

        Шаги:
            1. Авторизовать суперпользователя.
            2. Получить форму для создания мероприятия.
            3. Отправить PUT в /api/events/{published_event.id}.
            4. Проверить, что ответ 200.
            5. Проверить, что автор и название мероприятия правильные.
        """
        self.authenticate_admin()
        data = self.get_new_event_data(self.admin)
        url = reverse("event-detail", kwargs={"pk": self.published_event.id})  # type: ignore
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["author_info"]["username"], self.admin.username)  # type: ignore
        self.assertEqual(response.data["name"], data["name"])  # type: ignore

    def test_event_delete_user(self):
        """Тест DELETE запроса от обычного пользователя.

        Шаги:
            1. Авторизовать пользователя.
            2. Отправить DELETE в /api/events/{published_event.id}.
            2. Проверить, что ответ 403.
        """
        self.authenticate_user()
        url = reverse("event-detail", kwargs={"pk": self.published_event.id})  # type: ignore
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, 403)

    def test_event_delete_admin(self):
        """Тест DELETE запроса от суперпользователя.

        Шаги:
            1. Авторизовать суперпользователя.
            2. Отправить DELETE в /api/events/{published_event.id}.
            2. Проверить, что ответ 204.
        """
        self.authenticate_admin()
        url = reverse("event-detail", kwargs={"pk": self.published_event.id})  # type: ignore
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, 204)
