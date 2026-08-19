"""
Curated High-Resolution Destination Imagery
Provides reliable, aesthetic Unsplash photography for destination banners,
day headers, and hero prompt cards without requiring API keys.
"""

# High-resolution landscape photography for popular Indian and global destinations
DESTINATION_BANNERS: dict[str, str] = {
    # Indian Destinations
    "mumbai": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=1600&auto=format&fit=crop&q=80",
    "goa": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1600&auto=format&fit=crop&q=80",
    "delhi": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1600&auto=format&fit=crop&q=80",
    "new delhi": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1600&auto=format&fit=crop&q=80",
    "jaipur": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1600&auto=format&fit=crop&q=80",
    "rajasthan": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1600&auto=format&fit=crop&q=80",
    "kerala": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=1600&auto=format&fit=crop&q=80",
    "pune": "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?w=1600&auto=format&fit=crop&q=80",
    "bengaluru": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=1600&auto=format&fit=crop&q=80",
    "bangalore": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=1600&auto=format&fit=crop&q=80",
    "agra": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1600&auto=format&fit=crop&q=80",
    "varanasi": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=1600&auto=format&fit=crop&q=80",
    "manali": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1600&auto=format&fit=crop&q=80",
    "ladakh": "https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?w=1600&auto=format&fit=crop&q=80",
    "udaipur": "https://images.unsplash.com/photo-1615836245337-f5b9b2303f10?w=1600&auto=format&fit=crop&q=80",

    # Global Destinations
    "bali": "https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=1600&auto=format&fit=crop&q=80",
    "lisbon": "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1600&auto=format&fit=crop&q=80",
    "portugal": "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1600&auto=format&fit=crop&q=80",
    "tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1600&auto=format&fit=crop&q=80",
    "kyoto": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1600&auto=format&fit=crop&q=80",
    "japan": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1600&auto=format&fit=crop&q=80",
    "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1600&auto=format&fit=crop&q=80",
    "france": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1600&auto=format&fit=crop&q=80",
    "rome": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1600&auto=format&fit=crop&q=80",
    "italy": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=1600&auto=format&fit=crop&q=80",
    "barcelona": "https://images.unsplash.com/photo-1464790719320-516ecd75af6c?w=1600&auto=format&fit=crop&q=80",
    "spain": "https://images.unsplash.com/photo-1543783207-ec64e4d95325?w=1600&auto=format&fit=crop&q=80",
    "london": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1600&auto=format&fit=crop&q=80",
    "new york": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1600&auto=format&fit=crop&q=80",
    "nyc": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1600&auto=format&fit=crop&q=80",
    "dubai": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1600&auto=format&fit=crop&q=80",
    "singapore": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1600&auto=format&fit=crop&q=80",
    "bangkok": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=1600&auto=format&fit=crop&q=80",
    "thailand": "https://images.unsplash.com/photo-1528181304800-259b08848526?w=1600&auto=format&fit=crop&q=80",
    "vietnam": "https://images.unsplash.com/photo-1528127269322-539801943592?w=1600&auto=format&fit=crop&q=80",

    # Default scenic landscape
    "_default": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1600&auto=format&fit=crop&q=80",
}

# Category-specific aesthetic fallback photography
CATEGORY_IMAGES: dict[str, str] = {
    "attraction": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800&auto=format&fit=crop&q=80",
    "museum": "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=800&auto=format&fit=crop&q=80",
    "restaurant": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&auto=format&fit=crop&q=80",
    "cafe": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&auto=format&fit=crop&q=80",
    "viewpoint": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&auto=format&fit=crop&q=80",
    "park": "https://images.unsplash.com/photo-1448375240586-882707db888b?w=800&auto=format&fit=crop&q=80",
    "market": "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=800&auto=format&fit=crop&q=80",
    "bar": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=800&auto=format&fit=crop&q=80",
    "beach": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop&q=80",
    "default": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=800&auto=format&fit=crop&q=80",
}


def get_destination_banner(destination: str) -> str:
    """Resolve a wide 1600px hero cover photo for a destination."""
    if not destination:
        return DESTINATION_BANNERS["_default"]
    
    clean = destination.lower().strip()
    # Check exact match
    if clean in DESTINATION_BANNERS:
        return DESTINATION_BANNERS[clean]
    
    # Check individual token matches (e.g. 'Goa, India' -> 'goa')
    for part in clean.replace(",", " ").split():
        if part in DESTINATION_BANNERS:
            return DESTINATION_BANNERS[part]
            
    return DESTINATION_BANNERS["_default"]


def get_category_fallback_image(category: str) -> str:
    """Get a category-themed fallback photo URL."""
    cat = (category or "default").lower().strip()
    return CATEGORY_IMAGES.get(cat, CATEGORY_IMAGES["default"])
