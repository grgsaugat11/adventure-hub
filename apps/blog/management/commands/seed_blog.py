from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import Category, Post


STORIES = (
    {
        "slug": "everest-base-camp-trekking-tips",
        "title": "7 Essential Tips Before Trekking to Everest Base Camp",
        "category": "Adventure Tips",
        "excerpt": "From acclimatisation to packing light, here's how to prepare for your first journey into the Khumbu.",
        "image_alt": "A Himalayan village surrounded by mountain slopes",
        "body": (
            "Everest Base Camp is as much about the journey as the destination. Between Lukla and the foot of the world's highest mountain, you'll find forest trails, suspension bridges and villages where a warm cup of tea is part of the welcome. A little preparation helps you enjoy every step.\n\n"
            "1. Give yourself time to acclimatise. Build rest days into your itinerary, particularly around Namche Bazaar and Dingboche. Walk at a comfortable pace and remember that fitness doesn't prevent altitude sickness. Tell your guide if you feel unwell; worsening symptoms call for descent and medical advice, rather than pushing on.\n\n"
            "2. Train for consecutive walking days. Regular hikes with the boots and daypack you'll use on the trail are more useful than a single big workout. Include stairs or hills, and get used to walking on uneven ground.\n\n"
            "3. Pack layers, rather than one heavy outfit. Mornings can be cold while afternoons feel surprisingly warm. A base layer, insulating layer and weatherproof shell give you options. Add a warm hat, gloves and spare socks, and check your operator's seasonal kit list.\n\n"
            "4. Look after your feet. Break in your boots well before departure, keep socks dry and deal with hot spots before they turn into blisters. Carry a small personal first-aid kit and discuss any medication with a qualified clinician before your trip.\n\n"
            "5. Plan for changing mountain weather. Flights to and from Lukla are weather-dependent. Leave buffer days before an international flight and keep your schedule flexible. Your guide can explain alternatives if the route or transport needs to change.\n\n"
            "6. Carry a refillable bottle and a suitable water-treatment method. Ask your guide about safe drinking-water options along the route. Carry cash for personal purchases, as card payments and cash machines become less reliable higher up the valley.\n\n"
            "7. Travel with respect. Ask before photographing people, keep to the trail and take your rubbish with you. Choose local teahouses and take time to learn about Sherpa culture. The mountain views are unforgettable, but so are the people who make the journey possible."
        ),
    },
    {
        "slug": "pokhara-first-stop-nepal",
        "title": "Why Pokhara Should Be Your First Stop in Nepal",
        "category": "Destination Guide",
        "excerpt": "Peaceful lakes, mountain sunrises and easy-going cafés: meet Nepal's adventure capital.",
        "image_alt": "Paragliding above the Pokhara valley",
        "body": (
            "Pokhara invites you to slow down before you head into the mountains. Set beside Phewa Lake and backed by the Annapurna range, the city combines relaxed lakeside days with plenty of opportunities to get outdoors. It's a useful place to prepare for a trek, and an equally good place to unwind afterwards.\n\n"
            "Start with a morning beside Phewa Lake. Walk the lakeside path while the streets are still quiet, then stop for breakfast at a local café. Boat trips offer another perspective on the shoreline; choose an operator that provides a life jacket and follow local guidance about weather conditions.\n\n"
            "For mountain views, make time for Sarangkot at sunrise. Clear mornings can reveal a sweep of Himalayan peaks glowing above the valley. Cloud cover is part of mountain travel, so consider staying a few days rather than making the whole visit depend on one sunrise.\n\n"
            "A walk towards the World Peace Pagoda offers lake views and a different pace from Lakeside. Check the route and current trail conditions locally, carry water and allow time to return before dark. If you'd rather have a gentler day, explore the city's museums or find a quiet spot by the water.\n\n"
            "Pokhara is also a starting point for guided outdoor activities. Paragliding, day hikes and trips into the Annapurna foothills can fit into a longer stay. Talk to qualified local operators about requirements, equipment and weather before deciding what's right for you.\n\n"
            "Leave room for the everyday experiences too: a plate of fresh momos, an afternoon browsing small shops, or a conversation over tea. Three or four days gives you space to enjoy the city without treating it as just a stop on the way somewhere else."
        ),
    },
    {
        "slug": "nepal-beyond-the-mountains",
        "title": "Experiencing Nepal Beyond the Mountains",
        "category": "Culture",
        "excerpt": "Discover the temples, everyday traditions and local communities that make Nepal unforgettable.",
        "image_alt": "Traditional temple architecture in Nepal",
        "body": (
            "The Himalayas may bring you to Nepal, but the country's living culture gives you reasons to stay. In courtyards, markets and village kitchens, you'll find stories that don't fit into a mountain panorama. Leave a few days in your itinerary to discover them.\n\n"
            "Begin in the Kathmandu Valley. Kathmandu, Patan and Bhaktapur each offer a distinct rhythm, from busy squares to quieter lanes lined with workshops. Explore with a local guide who can explain the history of the buildings and the traditions that continue around them.\n\n"
            "Sacred places are part of everyday life. Around Buddhist stupas, follow the direction of local worshippers and keep a respectful distance from ceremonies. At Hindu temples, check entry rules before stepping inside. Modest clothing and asking before taking photographs are thoughtful habits wherever you visit.\n\n"
            "Food is another way to get to know a place. Try dal bhat, freshly made momos or a regional dish recommended by your host. A small local restaurant or a community-run homestay can offer a chance to learn about ingredients, recipes and the rhythm of a household.\n\n"
            "Festivals bring communities together, but their dates and customs vary. Ask locally about celebrations taking place during your stay, and remember that some rituals are personal rather than performances for visitors. Enjoy the atmosphere while following your host's guidance.\n\n"
            "Travel beyond the valley and the traditions change again. Tharu communities in the Terai and villages in the hills each have their own languages, crafts and histories. Choose experiences organised with the community, pay fairly for people's time and avoid assuming one visit tells the story of all Nepal.\n\n"
            "You don't need a packed cultural itinerary. Sometimes the most memorable moment is a conversation in a courtyard or watching an artisan at work. Make space to listen, ask questions with curiosity and let the journey move at a human pace."
        ),
    },
)


class Command(BaseCommand):
    help = "Create the three starter travel stories without overwriting existing articles."

    @transaction.atomic
    def handle(self, *args, **options):
        created_count = 0
        for index, story in enumerate(STORIES):
            data = story.copy()
            category_name = data.pop("category")
            category, _ = Category.objects.get_or_create(name=category_name)
            slug = data.pop("slug")
            _, created = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    **data,
                    "category": category,
                    "featured": True,
                    "is_published": True,
                    "published_at": datetime(2026, 7, 20 - index, tzinfo=timezone.utc),
                },
            )
            created_count += created
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} starter stories."))
