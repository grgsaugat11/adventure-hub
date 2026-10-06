from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import Category, Post


def post_list(request):
    posts = Post.objects.published().select_related("category")
    query = request.GET.get("q", "").strip()[:200]
    category_slug = request.GET.get("category", "").strip()
    selected_category = None

    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        posts = posts.filter(category=selected_category)
    if query:
        posts = posts.filter(
            Q(title__icontains=query)
            | Q(excerpt__icontains=query)
            | Q(body__icontains=query)
        )

    categories = Category.objects.annotate(
        post_count=Count(
            "posts",
            filter=Q(posts__is_published=True, posts__published_at__lte=timezone.now()),
        )
    ).filter(
        Q(post_count__gt=0)
        | Q(pk=selected_category.pk if selected_category else None)
    )
    page_obj = Paginator(posts, 6).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "pages/blog.html", {
        "page_obj": page_obj,
        "categories": categories,
        "selected_category": selected_category,
        "query": query,
        "filter_query": params.urlencode(),
    })


def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.published().select_related("category"), slug=slug
    )
    related_posts = (
        Post.objects.published()
        .filter(category=post.category)
        .exclude(pk=post.pk)
        .select_related("category")
    )[:3]
    return render(request, "pages/blog_detail.html", {
        "post": post,
        "related_posts": related_posts,
    })
