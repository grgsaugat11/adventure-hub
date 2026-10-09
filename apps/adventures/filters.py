from django.db.models import Case, CharField, Count, Value, When

# ===========================================
# FILTER HELPERS
#
# Kept out of views so they stay testable and
# reusable across listing / search endpoints.
# ===========================================


def apply_duration_filter(queryset, bucket):
    """Filter adventures into short / medium / long duration buckets."""
    if bucket == "short":
        return queryset.filter(duration_days__lte=4)
    if bucket == "medium":
        return queryset.filter(duration_days__gte=5, duration_days__lte=9)
    if bucket == "long":
        return queryset.filter(duration_days__gte=10)
    return queryset


def apply_price_filter(queryset, bucket):
    """Filter adventures into budget / standard / premium price buckets."""
    if bucket == "budget":
        return queryset.filter(price__lte=500)
    if bucket == "standard":
        return queryset.filter(price__gt=500, price__lte=1200)
    if bucket == "premium":
        return queryset.filter(price__gt=1200)
    return queryset


def apply_sort(queryset, sort):
    """Map a sort key to a stable ordering. Unknown keys fall back to recommended."""
    sorts = {
        "recommended": ("-featured", "-rating", "-review_count"),
        "rating": ("-rating",),
        "newest": ("-created_at",),
        "price_low": ("price",),
        "price_high": ("-price",),
    }
    ordering = sorts.get(sort or "recommended", sorts["recommended"])
    return queryset.order_by(*ordering, "pk")


# Computed SQL buckets so facet counts stay on the database side.
_DURATION_CASE = Case(
    When(duration_days__lte=4, then=Value("short")),
    When(duration_days__lte=9, then=Value("medium")),
    default=Value("long"),
    output_field=CharField(),
)

_PRICE_CASE = Case(
    When(price__lte=500, then=Value("budget")),
    When(price__lte=1200, then=Value("standard")),
    default=Value("premium"),
    output_field=CharField(),
)


def duration_bucket_counts(queryset):
    """{bucket_key: count} for a queryset, grouped via SQL CASE."""
    return dict(
        queryset.order_by().annotate(bucket=_DURATION_CASE)
        .values("bucket")
        .annotate(count=Count("id", distinct=True))
        .values_list("bucket", "count")
    )


def price_bucket_counts(queryset):
    """{bucket_key: count} for a queryset, grouped via SQL CASE."""
    return dict(
        queryset.order_by().annotate(bucket=_PRICE_CASE)
        .values("bucket")
        .annotate(count=Count("id", distinct=True))
        .values_list("bucket", "count")
    )
