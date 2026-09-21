import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.adventures.models import Activity, Adventure, Region

# Slug -> {region, activities, ...}
ADVENTURES = (
    {
        "title": "Everest Base Camp Trek",
        "slug": "everest-base-camp-trek",
        "short_description": "Trek to the roof of the world through Sherpa villages and Khumbu's iconic glacial valleys.",
        "overview": (
            "Follow in the footsteps of mountaineering history on the world's most celebrated trek. "
            "Fly into Lukla, climb through the rhododendron forests of Namche Bazaar, and stand at the "
            "foot of the world's highest peak at 5,364m. Rest days aid acclimatisation while the teahouse "
            "warmth of Tengboche and Gorak Shep frames views of Ama Dablam and the Khumbu Icefall."
        ),
        "region": "everest",
        "activities": ["trekking"],
        "difficulty": "challenging",
        "duration_days": 12,
        "price": "1299",
        "max_group_size": 14,
        "image": "images/everest.jpg",
        "rating": "4.9",
        "review_count": 214,
        "featured": True,
    },
    {
        "title": "Annapurna Circuit Trek",
        "slug": "annapurna-circuit-trek",
        "short_description": "Cross Thorong La and descend through the dramatic Kali Gandaki gorge.",
        "overview": (
            "Nepal's classic round of the Annapurna massif delivers the greatest variety in trekking: "
            "subtropical jungle, Tibetan-style villages, and the arid windswept plateau of Thorong La. "
            "After crossing the pass at 5,416m, descend the world's deepest gorge past Marpha's apple "
            "orchards and Jomsom's dramatic desert canyons."
        ),
        "region": "annapurna",
        "activities": ["trekking", "hiking"],
        "difficulty": "challenging",
        "duration_days": 10,
        "price": "999",
        "max_group_size": 12,
        "image": "images/annapurna.jpg",
        "rating": "4.8",
        "review_count": 189,
        "featured": True,
    },
    {
        "title": "Chitwan Jungle Safari",
        "slug": "chitwan-jungle-safari",
        "short_description": "Track rhinos, elephants and Bengal tigers through Chitwan National Park.",
        "overview": (
            "Venture deep into one of Asia's finest national parks aboard a jeep or on foot with expert "
            "local guides. Paddle by canoe along the Rapti river at dawn, cruise for one-horned rhinos, "
            "and end the day with an authentic Tharu cultural dance in Sauraha."
        ),
        "region": "chitwan-terai",
        "activities": ["jungle-safari"],
        "difficulty": "easy",
        "duration_days": 3,
        "price": "399",
        "max_group_size": 16,
        "image": "images/chitwan.jpg",
        "rating": "4.7",
        "review_count": 342,
        "featured": True,
    },
    {
        "title": "Langtang Valley Trek",
        "slug": "langtang-valley-trek",
        "short_description": "A wild, glacier-capped valley trek close to Kathmandu with genuine village homestays.",
        "overview": (
            "Hidden beyond the Trisuli river, Langtang Valley offers towering peaks, yak pastures and "
            "some of Nepal's warmest hospitality. Trek from the Buddhist town of Kyanjin Gompa towards "
            "the Langtang glacier while black-faced langurs bound across the hillsides below."
        ),
        "region": "langtang",
        "activities": ["trekking", "hiking"],
        "difficulty": "moderate",
        "duration_days": 7,
        "price": "649",
        "max_group_size": 12,
        "image": "images/popular/mountain.jpg",
        "rating": "4.8",
        "review_count": 156,
        "featured": False,
    },
    {
        "title": "Pokhara Valley Highlights",
        "slug": "pokhara-valley-highlights",
        "short_description": "Lakes, caves and sunrise over the Annapurnas from the city of lakes.",
        "overview": (
            "Soak up the lakeside charm of Pokhara and its palm-fringed Phewa Tal. Hike to the World "
            "Peace Pagoda for a full panorama of the Annapurna range, explore the vast Gupteshwor caves, "
            "and drive to Sarangkot at dawn for a golden-hued sunrise over the Himalaya."
        ),
        "region": "pokhara-gandaki",
        "activities": ["hiking", "cultural-tour"],
        "difficulty": "easy",
        "duration_days": 4,
        "price": "289",
        "max_group_size": 16,
        "image": "images/popular/lakeside.jpg",
        "rating": "4.6",
        "review_count": 298,
        "featured": False,
    },
    {
        "title": "Upper Mustang Trek",
        "slug": "upper-mustang-trek",
        "short_description": "A restricted Himalayan trans-Himalayan kingdom of caves, chortens and desert cliffs.",
        "overview": (
            "Enter the forbidden kingdom of Lo Manthang, where Tibetan culture survives unchanged behind "
            "high canyon walls. Ride the wind through ochre badlands of eroded rock, whitewashed "
            "monasteries and sky caves, all beneath the 8,000m wall of Annapurna and Dhaulagiri."
        ),
        "region": "mustang",
        "activities": ["trekking", "cultural-tour"],
        "difficulty": "challenging",
        "duration_days": 14,
        "price": "1599",
        "max_group_size": 10,
        "image": "images/popular/uppermustang.jpg",
        "rating": "4.9",
        "review_count": 87,
        "featured": True,
    },
    {
        "title": "Bardia National Park Safari",
        "slug": "bardia-national-park-safari",
        "short_description": "Nepal's wildest, least-visited park — best odds of sighting a tiger.",
        "overview": (
            "Far from the crowds, remote Bardia packs the highest density of wildlife in Nepal. "
            "Traverse the sal forests and grasslands by jeep and elephant, keeping your eyes peeled for "
            "Bengal tigers, wild elephants and the endangered Gangetic dolphin that swims the nearby Karnali."
        ),
        "region": "karnali",
        "activities": ["jungle-safari"],
        "difficulty": "easy",
        "duration_days": 5,
        "price": "449",
        "max_group_size": 12,
        "image": "images/popular/safari.jpg",
        "rating": "4.7",
        "review_count": 164,
        "featured": False,
    },
    {
        "title": "Kathmandu Heritage Walk",
        "slug": "kathmandu-heritage-walk",
        "short_description": "Guided walk through three UNESCO World Heritage squares in the Kathmandu Valley.",
        "overview": (
            "Step into the living history of Durbar Squares at Kathmandu, Patan and Bhaktapur — ornate "
            "Newari temples, palace courtyards and bustling markets. Finish with the monkey-laden stupa "
            "of Swayambhunath as the valley lights begin to twinkle below."
        ),
        "region": "kathmandu-valley",
        "activities": ["cultural-tour"],
        "difficulty": "easy",
        "duration_days": 2,
        "price": "199",
        "max_group_size": 20,
        "image": "images/blog/temple.jpg",
        "rating": "4.8",
        "review_count": 410,
        "featured": False,
    },
    {
        "title": "Pokhara Paragliding Experience",
        "slug": "pokhara-paragliding-experience",
        "short_description": "Soar over Phewa Lake with professional tandem pilots and an Annapurna backdrop.",
        "overview": (
            "Launch from Sarangkot's grassy ridge and drift on thermals with a certified tandem pilot, "
            "looking straight across to Annapurna and Machhapuchhre. The gentle 30-minute flight touches "
            "down beside Phewa Lake, with the option to add extra surfing time for high-altitude thrills."
        ),
        "region": "pokhara-gandaki",
        "activities": ["paragliding"],
        "difficulty": "easy",
        "duration_days": 1,
        "price": "129",
        "max_group_size": 8,
        "image": "images/blog/paragliding.jpg",
        "rating": "4.9",
        "review_count": 523,
        "featured": True,
    },
    {
        "title": "Ghandruk Village Trek",
        "slug": "ghandruk-village-trek",
        "short_description": "A short Annapurna foothills trek staying in warm Gurung homestays.",
        "overview": (
            "An off-the-beaten-path ramble from Phedi through terraced hillsides to the stone-and-slate "
            "village of Ghandruk, with its landmark Gurung farming museum. Sleep in family-run homestays, "
            "share dal bhat with hosts, and wake to sunrise views of Machhapuchhre and the Annapurna giants."
        ),
        "region": "annapurna",
        "activities": ["trekking", "homestay"],
        "difficulty": "moderate",
        "duration_days": 5,
        "price": "549",
        "max_group_size": 10,
        "image": "images/blog/village.jpg",
        "rating": "4.7",
        "review_count": 98,
        "featured": True,
    },
    {
        "title": "Manaslu Circuit Trek",
        "slug": "manaslu-circuit-trek",
        "short_description": "A remote, restricted trek around the world's eighth-highest mountain.",
        "overview": (
            "No roads, few people and the towering 8,163m face of Manaslu for company. This culturally "
            "and ecologically varied circuit crosses the Larkya La at 5,106m and links Buddhist villages "
            "with glacier-fed rivers, providing a wilder, quieter counterpart to the neighbouring circuits."
        ),
        "region": "manaslu",
        "activities": ["trekking", "climbing"],
        "difficulty": "difficult",
        "duration_days": 16,
        "price": "1799",
        "max_group_size": 10,
        "image": "images/mountain.jpg",
        "rating": "4.8",
        "review_count": 64,
        "featured": False,
    },
    {
        "title": "Nagarkot Sunrise Cycling Tour",
        "slug": "nagarkot-sunrise-cycling-tour",
        "short_description": "Ride to Nagarkot's viewpoint and watch the sun rise over the Everest range.",
        "overview": (
            "Drink in the Himalayan panorama from Nagarkot — an 8,000ft sunrise viewpoint where, on clear "
            "days, you can see from Everest to Annapurna. Wind back down through terraced villages and "
            "Tibetan settlements on a leisurely supported ride that suits first-time mountain cyclists."
        ),
        "region": "kathmandu-valley",
        "activities": ["cycling", "hiking"],
        "difficulty": "easy",
        "duration_days": 1,
        "price": "89",
        "max_group_size": 15,
        "image": "images/sunset.jpg",
        "rating": "4.6",
        "review_count": 230,
        "featured": False,
    },
)

REGIONS = (
    ("everest", "Everest Region", "Sagarmatha and Khumbu Himalaya", 1, "images/everest.jpg"),
    ("annapurna", "Annapurna Region", "Annapurna Himalaya and the Kali Gandaki", 2, "images/annapurna.jpg"),
    ("langtang", "Langtang Region", "The close-to-Kathmandu Langtang Himal", 3, "images/popular/mountain.jpg"),
    ("mustang", "Mustang Region", "The trans-Himalayan rain shadow", 4, "images/popular/uppermustang.jpg"),
    ("manaslu", "Manaslu Region", "Remote border country of Gorkha", 5, "images/mountain.jpg"),
    ("kathmandu-valley", "Kathmandu Valley", "Heritage squares and valley towns", 6, "images/blog/temple.jpg"),
    ("pokhara-gandaki", "Pokhara & Gandaki", "Lakes, bazaars and Phewa Tal", 7, "images/popular/lakeside.jpg"),
    ("chitwan-terai", "Chitwan & Terai", "Jungle parks of the lowlands", 8, "images/chitwan.jpg"),
    ("karnali", "Karnali & Far West", "The wild, hidden west", 9, "images/popular/safari.jpg"),
)

ACTIVITIES = (
    "Trekking",
    "Hiking",
    "Jungle Safari",
    "Paragliding",
    "Cultural Tour",
    "Mountain Biking",
    "Cycling",
    "Homestay",
    "Climbing",
    "White Water Rafting",
)


class Command(BaseCommand):
    help = "Seed regions, activities and a realistic catalogue of adventures."

    def _copy_image(self, source, slug, subdir="adventures"):
        """Copy a static seed image into media once, returning the stored path."""
        target_dir = Path(settings.MEDIA_ROOT) / subdir
        target = target_dir / f"{slug}.jpg"
        if not target.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            src = Path(settings.STATICFILES_DIRS[0]) / source
            if src.exists():
                shutil.copy2(src, target)
                self.stdout.write(f"  copied image -> {target.relative_to(settings.MEDIA_ROOT)}")
            else:
                self.stdout.write(self.style.WARNING(f"  image missing: {source}"))
        return f"{subdir}/{slug}.jpg" if target.exists() else ""

    @transaction.atomic
    def handle(self, *args, **options):
        activity_map = {}
        for name in ACTIVITIES:
            activity, _ = Activity.objects.update_or_create(name=name)
            activity_map[activity.slug] = activity

        region_map = {}
        for slug, name, desc, order, source in REGIONS:
            image = self._copy_image(source, slug, subdir="destinations")
            region, _ = Region.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": desc,
                    "ordering": order,
                    "image": image,
                    "image_alt": name,
                },
            )
            region_map[slug] = region

        for item in ADVENTURES:
            activity_slugs = item["activities"]
            slug = item["slug"]
            image = self._copy_image(item["image"], slug)

            adventure, created = Adventure.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": item["title"],
                    "short_description": item["short_description"],
                    "overview": item["overview"],
                    "region": region_map[item["region"]],
                    "difficulty": item["difficulty"],
                    "duration_days": item["duration_days"],
                    "price": item["price"],
                    "max_group_size": item["max_group_size"],
                    "image": image,
                    "image_alt": item["title"],
                    "rating": item["rating"],
                    "review_count": item["review_count"],
                    "featured": item["featured"],
                    "is_active": True,
                },
            )
            adventure.activities.set([activity_map[s] for s in activity_slugs])
            status = "created" if created else "updated"
            self.stdout.write(self.style.SUCCESS(f"  {status}: {adventure.title}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. {Adventure.objects.count()} adventures, "
                f"{Region.objects.count()} regions, {Activity.objects.count()} activities."
            )
        )