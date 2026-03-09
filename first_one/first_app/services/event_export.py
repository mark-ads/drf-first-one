from io import BytesIO
from typing import cast

from django.db.models import QuerySet
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from first_one.first_app.models import Event


class EventExportService:
    def __init__(self, queryset: QuerySet[Event]):
        self.queryset = queryset

    def run(self) -> BytesIO:
        """Создает XLSX файл и возвращает как BytesIO."""
        workbook = Workbook()
        sheet = cast(Worksheet, workbook.active)  # cast, чтобы подсказать тип LSP
        sheet.title = "Events"

        headers = [
            "Название мероприятия",
            "Описание мероприятия",
            "Дата публикации",
            "Дата начала",
            "Дата завершения",
            "Название места проведения",
            "Широта",
            "Долгота",
            "Рейтинг",
        ]

        sheet.append(headers)

        for event in self.queryset.select_related("place"):
            row = [
                event.name,
                event.description,
                event.publish_date,
                event.start_date,
                event.end_date,
                event.place.name,
                event.place.latitude,
                event.place.longitude,
                event.rating,
            ]
            sheet.append(row)

        new_file = BytesIO()  # создаем буфер для будущего файла
        workbook.save(new_file)  # сохраняем в буфер
        new_file.seek(0)  # возвращаем указатель буфера в начало файла

        return new_file
