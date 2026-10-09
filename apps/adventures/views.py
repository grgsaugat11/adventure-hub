from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView

from .filters import (
    apply_duration_filter,
    apply_price_filter,
    apply_sort,
    duration_bucket_counts,
    price_bucket_counts,
)
from .models import (
    Activity,
    Adventure,
    DURATION_BUCKETS,
    PRICE_BUCKETS,
    Region,
)

# Every filter group resolved by _apply_facet.
FACETS = ("q", "region", "difficulty", "activity", "duration", "price")


class AdventureListView(ListView):
    model = Adventure
    template_name = "pages/adventures.html"
    context_object_name = "adventures"
    paginate_by = 9

    # -----------------------------------------------------
    # Core filtering
    # -----------------------------------------------------

    def _apply_facet(self, queryset, name, value):
        value = (value or "").strip()
        if not value:
            return queryset

        if name == "q":
            return queryset.filter(
                Q(title__icontains=value)
                | Q(short_description__icontains=value)
                | Q(overview__icontains=value)
                | Q(region__name__icontains=value)
            )
        if name == "region":
            return queryset.filter(region__slug=value)
        if name == "difficulty":
            return queryset.filter(difficulty=value)
        if name == "activity":
            return queryset.filter(activities__slug=value)
        if name == "duration":
            return apply_duration_filter(queryset, value)
        if name == "price":
            return apply_price_filter(queryset, value)
        return queryset

    def _facet_base(self, exclude):
        """All published adventures with every filter applied except `exclude`.

        This powers dependent facet counts: when computing a region's count,
        the current region selection is excluded so its group always reflects
        the remaining criteria.
        """
        params = self.request.GET
        queryset = Adventure.objects.filter(is_active=True)
        for name in FACETS:
            if name == exclude:
                continue
            queryset = self._apply_facet(queryset, name, params.get(name))
        # DISTINCT must not pull default ordering columns into facet groups.
        return queryset.order_by().distinct()

    def get_queryset(self):
        params = self.request.GET
        queryset = (
            Adventure.objects.filter(is_active=True)
            .select_related("region")
            .prefetch_related("activities")
        )
        for name in FACETS:
            queryset = self._apply_facet(queryset, name, params.get(name))
        return apply_sort(queryset.distinct(), params.get("sort"))

    # -----------------------------------------------------
    # Context
    # -----------------------------------------------------

    def _remove_param(self, params, name):
        query = params.copy()
        query.pop(name, None)
        query.pop("page", None)
        return query.urlencode()

    def _set_param(self, params, name, value):
        query = params.copy()
        query[name] = value
        query.pop("page", None)
        return query.urlencode()

    def _toggle_href(self, params, name, value):
        """URL params that set the facet, or remove it when already selected."""
        if params.get(name) == value:
            return self._remove_param(params, name)
        return self._set_param(params, name, value)

    def _active_filters(self, params):
        difficulty_labels = dict(Adventure.Difficulty.choices)
        duration_labels, price_labels = dict(DURATION_BUCKETS), dict(PRICE_BUCKETS)

        region_slugs = params.get("region", "").strip()
        region_names = {r.slug: r.name for r in Region.objects.all()} if region_slugs else {}
        activity_slugs = params.get("activity", "").strip()
        activity_names = {a.slug: a.name for a in Activity.objects.all()} if activity_slugs else {}

        resolved = {
            "q": lambda v: f'Search: "{v}"',
            "region": lambda v: region_names.get(v, v),
            "difficulty": lambda v: difficulty_labels.get(v, v),
            "activity": lambda v: activity_names.get(v, v),
            "duration": lambda v: duration_labels.get(v, v),
            "price": lambda v: price_labels.get(v, v),
        }

        filters = []
        for key, raw in params.lists():
            if key in ("page", "sort"):
                continue
            for value in raw:
                value = value.strip()
                if not value or key not in resolved:
                    continue
                filters.append(
                    {"label": resolved[key](value), "remove_url": self._remove_param(params, key)}
                )
        return filters

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Preserve every current query parameter across pagination links.
        preserved = self.request.GET.copy()
        preserved.pop("page", None)
        context["query_string"] = preserved.urlencode()

        context["active_filters"] = self._active_filters(self.request.GET)

        # Facet options that belong to DB rows share one structure.
        region_rows = self._facet_base("region").values(
            "region_id", "region__slug", "region__name"
        ).annotate(count=Count("id", distinct=True)).order_by("region__name")
        activity_rows = self._facet_base("activity").filter(activities__isnull=False).values(
            "activities__id", "activities__slug", "activities__name"
        ).annotate(count=Count("id", distinct=True)).order_by("activities__name")

        duration_counts = duration_bucket_counts(self._facet_base("duration"))
        price_counts = price_bucket_counts(self._facet_base("price"))
        difficulty_counts = {
            item["difficulty"]: item["count"]
            for item in self._facet_base("difficulty").values("difficulty").annotate(count=Count("id", distinct=True))
        }

        params = self.request.GET

        context["regions"] = [
            {
                "name": row["region__name"],
                "count": row["count"],
                "selected": params.get("region") == row["region__slug"],
                "href": self._toggle_href(params, "region", row["region__slug"]),
            }
            for row in region_rows
        ]
        context["activities"] = [
            {
                "name": row["activities__name"],
                "count": row["count"],
                "selected": params.get("activity") == row["activities__slug"],
                "href": self._toggle_href(params, "activity", row["activities__slug"]),
            }
            for row in activity_rows
        ]
        context["difficulties"] = [
            {
                "key": key,
                "name": name,
                "count": difficulty_counts.get(key, 0),
                "selected": params.get("difficulty") == key,
                "href": self._toggle_href(params, "difficulty", key),
            }
            for key, name in Adventure.Difficulty.choices
        ]
        context["durations"] = [
            {
                "key": key,
                "name": name,
                "count": duration_counts.get(key, 0),
                "selected": params.get("duration") == key,
                "href": self._toggle_href(params, "duration", key),
            }
            for key, name in DURATION_BUCKETS
        ]
        context["prices"] = [
            {
                "key": key,
                "name": name,
                "count": price_counts.get(key, 0),
                "selected": params.get("price") == key,
                "href": self._toggle_href(params, "price", key),
            }
            for key, name in PRICE_BUCKETS
        ]
        return context


def adventure_detail(request, slug):
    adventure = get_object_or_404(
        Adventure.objects.select_related("region").prefetch_related("activities"),
        slug=slug,
        is_active=True,
    )
    related = (
        Adventure.objects.filter(is_active=True, region=adventure.region)
        .select_related("region")
        .exclude(pk=adventure.pk)[:3]
    )
    return render(
        request,
        "pages/adventure_detail.html",
        {
            "adventure": adventure,
            "related_adventures": related,
        },
    )
