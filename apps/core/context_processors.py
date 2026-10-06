from django.conf import settings


def site_details(request):
    return {
        "site_contact_email": settings.SITE_CONTACT_EMAIL,
        "site_contact_phone": settings.SITE_CONTACT_PHONE,
        "site_social_links": settings.SITE_SOCIAL_LINKS,
    }
