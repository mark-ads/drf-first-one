import django_filters

from first_one.first_app.models import Event, EventPlace


class EventFilter(django_filters.FilterSet):
    publish_date_after = django_filters.IsoDateTimeFilter(
        field_name="publish_date", lookup_expr="gte"
    )

    publish_date_before = django_filters.IsoDateTimeFilter(
        field_name="publish_date", lookup_expr="lte"
    )

    start_date_after = django_filters.IsoDateTimeFilter(
        field_name="start_date", lookup_expr="gte"
    )

    start_date_before = django_filters.IsoDateTimeFilter(
        field_name="start_date", lookup_expr="lte"
    )

    end_date_after = django_filters.IsoDateTimeFilter(
        field_name="end_date", lookup_expr="gte"
    )

    end_date_before = django_filters.IsoDateTimeFilter(
        field_name="end_date", lookup_expr="lte"
    )

    place = django_filters.ModelMultipleChoiceFilter(
        field_name="place", queryset=EventPlace.objects.all()
    )

    rating = django_filters.RangeFilter(field_name="rating")

    class Meta:
        model = Event
        fields = []


class EventNotificationFilter(django_filters.FilterSet):
    event = django_filters.ModelMultipleChoiceFilter(
        field_name="event",
        queryset=Event.objects.filter(status=Event.StatusChoices.DRAFT),
    )
