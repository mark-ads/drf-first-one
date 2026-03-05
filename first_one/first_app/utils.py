from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image


def create_preview(image_path: str) -> ContentFile:
    """Форматировать исходное изображение в превью.

    Превью имеет наименьшую сторону в 200px.
    """
    image = Image.open(image_path)
    sizes = image.size
    if min(sizes) >= 200:
        if sizes[0] <= sizes[1]:
            image.thumbnail((200, sizes[1]))
        else:
            image.thumbnail((sizes[0], 200))
    buffer = BytesIO()
    format = image.format or "JPEG"
    image.save(buffer, format=format)
    return ContentFile(buffer.getvalue())
