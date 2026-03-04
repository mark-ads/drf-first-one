from django.contrib.auth.models import User

from first_one.first_app.models import EventPlace

if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser("admin", password="admin")

admin = User.objects.get(username="admin")

places_names = ['Ранчо', 'Кубеково', "Сибирский Сафари клуб"]

places = []

for i in range(3):
    place = EventPlace.objects.create()
