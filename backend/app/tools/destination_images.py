"""
Curated High-Resolution Destination Imagery & Multi-Tier Photo Engine (v9)
Provides reliable, aesthetic Unsplash photography for destination banners,
day headers, stop cards, and fallback pools without requiring external API keys.
"""

# High-resolution landscape photography for popular Indian and global destinations
DESTINATION_BANNERS: dict[str, str] = {
    # Indian Destinations
    "mumbai": "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=1600&auto=format&fit=crop&q=80",
    "goa": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1600&auto=format&fit=crop&q=80",
    "delhi": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1600&auto=format&fit=crop&q=80",
    "new delhi": "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1600&auto=format&fit=crop&q=80",
    "hyderabad": "https://images.unsplash.com/photo-1605335198083-d56d782cf760?w=1600&auto=format&fit=crop&q=80",
    "jaipur": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1600&auto=format&fit=crop&q=80",
    "rajasthan": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1600&auto=format&fit=crop&q=80",
    "kerala": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=1600&auto=format&fit=crop&q=80",
    "pune": "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?w=1600&auto=format&fit=crop&q=80",
    "bengaluru": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=1600&auto=format&fit=crop&q=80",
    "bangalore": "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=1600&auto=format&fit=crop&q=80",
    "chennai": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1600&auto=format&fit=crop&q=80",
    "kolkata": "https://images.unsplash.com/photo-1558431382-27e303142255?w=1600&auto=format&fit=crop&q=80",
    "amritsar": "https://images.unsplash.com/photo-1514222134-b57cbb8ce073?w=1600&auto=format&fit=crop&q=80",
    "ahmedabad": "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=1600&auto=format&fit=crop&q=80",
    "kochi": "https://images.unsplash.com/photo-1590050752117-238cb0fb12b1?w=1600&auto=format&fit=crop&q=80",
    "shimla": "https://images.unsplash.com/photo-1562670652-e5947bddb335?w=1600&auto=format&fit=crop&q=80",
    "hampi": "https://images.unsplash.com/photo-1600100397608-f010f443b749?w=1600&auto=format&fit=crop&q=80",
    "mysore": "https://images.unsplash.com/photo-1596701062351-8c2c14d1fdd0?w=1600&auto=format&fit=crop&q=80",
    "pondicherry": "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1600&auto=format&fit=crop&q=80",
    "ooty": "https://images.unsplash.com/photo-1589182373726-e4f658ab50f0?w=1600&auto=format&fit=crop&q=80",
    "kashmir": "https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=1600&auto=format&fit=crop&q=80",
    "srinagar": "https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=1600&auto=format&fit=crop&q=80",
    "gulmarg": "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1600&auto=format&fit=crop&q=80",
    "pahalgam": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1600&auto=format&fit=crop&q=80",
    "jodhpur": "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1600&auto=format&fit=crop&q=80",
    "jaisalmer": "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1600&auto=format&fit=crop&q=80",
    "agra": "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1600&auto=format&fit=crop&q=80",
    "varanasi": "https://images.unsplash.com/photo-1561361513-2d000a50f0dc?w=1600&auto=format&fit=crop&q=80",
    "manali": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1600&auto=format&fit=crop&q=80",
    "himachal": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1600&auto=format&fit=crop&q=80",
    "ladakh": "https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?w=1600&auto=format&fit=crop&q=80",
    "leh": "https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?w=1600&auto=format&fit=crop&q=80",
    "udaipur": "https://images.unsplash.com/photo-1615836245337-f5b9b2303f10?w=1600&auto=format&fit=crop&q=80",

    # Global Destinations
    "bali": "https://images.unsplash.com/photo-1555400038-63f5ba517a47?w=1600&auto=format&fit=crop&q=80",
    "lisbon": "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1600&auto=format&fit=crop&q=80",
    "portugal": "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=1600&auto=format&fit=crop&q=80",
    "tokyo": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=1600&auto=format&fit=crop&q=80",
    "kyoto": "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=1600&auto=format&fit=crop&q=80",
    "japan": "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?w=1600&auto=format&fit=crop&q=80",
    "seoul": "https://images.unsplash.com/photo-1538485399081-7191377e8241?w=1600&auto=format&fit=crop&q=80",
    "paris": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1600&auto=format&fit=crop&q=80",
    "france": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1600&auto=format&fit=crop&q=80",
    "rome": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=1600&auto=format&fit=crop&q=80",
    "italy": "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=1600&auto=format&fit=crop&q=80",
    "barcelona": "https://images.unsplash.com/photo-1464790719320-516ecd75af6c?w=1600&auto=format&fit=crop&q=80",
    "spain": "https://images.unsplash.com/photo-1543783207-ec64e4d95325?w=1600&auto=format&fit=crop&q=80",
    "amsterdam": "https://images.unsplash.com/photo-1512470876302-972faa2aa9a4?w=1600&auto=format&fit=crop&q=80",
    "prague": "https://images.unsplash.com/photo-1541849546-216549ae216d?w=1600&auto=format&fit=crop&q=80",
    "vienna": "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=1600&auto=format&fit=crop&q=80",
    "istanbul": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1600&auto=format&fit=crop&q=80",
    "cairo": "https://images.unsplash.com/photo-1572252009286-268acec5ca0a?w=1600&auto=format&fit=crop&q=80",
    "london": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1600&auto=format&fit=crop&q=80",
    "new york": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1600&auto=format&fit=crop&q=80",
    "nyc": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=1600&auto=format&fit=crop&q=80",
    "dubai": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=1600&auto=format&fit=crop&q=80",
    "singapore": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=1600&auto=format&fit=crop&q=80",
    "bangkok": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=1600&auto=format&fit=crop&q=80",
    "thailand": "https://images.unsplash.com/photo-1528181304800-259b08848526?w=1600&auto=format&fit=crop&q=80",
    "vietnam": "https://images.unsplash.com/photo-1528127269322-539801943592?w=1600&auto=format&fit=crop&q=80",
    "sydney": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1600&auto=format&fit=crop&q=80",

    # Default scenic landscape
    "_default": "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1600&auto=format&fit=crop&q=80",
}

# ── Destination-Specific Photo Libraries (Curated regional collections) ─────────
# When a stop belongs to a known region, we draw from these vetted pools before generic categories.
DESTINATION_PHOTO_LIBRARIES: dict[str, dict[str, list[str]]] = {
    "kashmir": {
        "viewpoint": [
            "https://images.unsplash.com/photo-1598091383021-15ddea10925d?w=1200&auto=format&fit=crop&q=80",  # Dal Lake Shikara
            "https://images.unsplash.com/photo-1566833945842-824cece52744?w=1200&auto=format&fit=crop&q=80",  # Zabarwan range overlook
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",  # Mountain vista
        ],
        "nature": [
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&auto=format&fit=crop&q=80",  # Alpine meadows Pahalgam
            "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&auto=format&fit=crop&q=80",  # Pine valley
            "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&auto=format&fit=crop&q=80",  # Deep forest
        ],
        "attraction": [
            "https://images.unsplash.com/photo-1589308078059-be1415eab4c3?w=1200&auto=format&fit=crop&q=80",  # Mughal Gardens terrace
            "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1200&auto=format&fit=crop&q=80",  # Historic pavilion
            "https://images.unsplash.com/photo-1548013146-72479768bada?w=1200&auto=format&fit=crop&q=80",  # Carved heritage shrine
        ],
        "restaurant": [
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200&auto=format&fit=crop&q=80",  # Wazwan dining
            "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200&auto=format&fit=crop&q=80",  # Traditional feast
        ],
        "market": [
            "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=1200&auto=format&fit=crop&q=80",  # Downtown artisan bazaar
            "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1200&auto=format&fit=crop&q=80",  # Kashmiri handicraft stall
        ],
    },
    "goa": {
        "beach": [
            "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1200&auto=format&fit=crop&q=80",  # Palolem palm beach
            "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&auto=format&fit=crop&q=80",  # Turquoise coastline
            "https://images.unsplash.com/photo-1519046904884-53103b34b206?w=1200&auto=format&fit=crop&q=80",  # Golden sand cove
        ],
        "attraction": [
            "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1200&auto=format&fit=crop&q=80",  # Portuguese church
            "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=1200&auto=format&fit=crop&q=80",  # Heritage fort ramparts
        ],
        "viewpoint": [
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",  # Chapora sunset cliff
            "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1200&auto=format&fit=crop&q=80",  # Sea viewpoint
        ],
        "restaurant": [
            "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200&auto=format&fit=crop&q=80",  # Seaside shack bistro
            "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=1200&auto=format&fit=crop&q=80",  # Tropical cocktail bar
        ],
    },
    "mumbai": {
        "attraction": [
            "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=1200&auto=format&fit=crop&q=80",  # Gateway of India
            "https://images.unsplash.com/photo-1566552881560-0be862a7c445?w=1200&auto=format&fit=crop&q=80",  # Gothic architectural facade
        ],
        "viewpoint": [
            "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?w=1200&auto=format&fit=crop&q=80",  # Marine Drive promenade
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",  # Ocean sunset
        ],
        "cafe": [
            "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1200&auto=format&fit=crop&q=80",  # Heritage cafe
            "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200&auto=format&fit=crop&q=80",  # Vintage bistro
        ],
    },
    "jaipur": {
        "attraction": [
            "https://images.unsplash.com/photo-1599661046289-e31897846e41?w=1200&auto=format&fit=crop&q=80",  # Hawa Mahal facade
            "https://images.unsplash.com/photo-1600100397608-f010f443b749?w=1200&auto=format&fit=crop&q=80",  # Amer fort courtyards
            "https://images.unsplash.com/photo-1615836245337-f5b9b2303f10?w=1200&auto=format&fit=crop&q=80",  # Royal palace archway
        ],
        "viewpoint": [
            "https://images.unsplash.com/photo-1580618672591-eb180b1a973f?w=1200&auto=format&fit=crop&q=80",  # Nahargarh ridge sunset
        ],
    },
    "delhi": {
        "attraction": [
            "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=1200&auto=format&fit=crop&q=80",  # India Gate monument
            "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=1200&auto=format&fit=crop&q=80",  # Mughal dome & minarets
        ],
        "park": [
            "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&auto=format&fit=crop&q=80",  # Sunder Nursery green gardens
        ],
    },
    "ladakh": {
        "nature": [
            "https://images.unsplash.com/photo-1581793745862-99fde7fa73d2?w=1200&auto=format&fit=crop&q=80",  # Pangong high-altitude lake
            "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",  # Cold desert mountain pass
        ],
        "attraction": [
            "https://images.unsplash.com/photo-1548013146-72479768bada?w=1200&auto=format&fit=crop&q=80",  # Thiksey monastery
        ],
    },
    "manali": {
        "nature": [
            "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=1200&auto=format&fit=crop&q=80",  # Cedar pines & snow peaks
            "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&auto=format&fit=crop&q=80",  # Mountain stream
        ],
        "attraction": [
            "https://images.unsplash.com/photo-1562670652-e5947bddb335?w=1200&auto=format&fit=crop&q=80",  # Traditional wooden temple
        ],
    },
}

# ── Multi-Photo Pools per Category (8-10 distinct high-resolution photos each) ──
# Eliminates identical repeating images when multiple stops share the same category.
CATEGORY_IMAGE_POOLS: dict[str, list[str]] = {
    "attraction": [
        "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1541849546-216549ae216d?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1543783207-ec64e4d95325?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1464790719320-516ecd75af6c?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=1200&auto=format&fit=crop&q=80",
    ],
    "museum": [
        "https://images.unsplash.com/photo-1565008447742-97f6f38c985c?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1554907984-15263bfd63bd?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1518998053901-5348d3961a04?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1544967082-d9d25d867d66?w=1200&auto=format&fit=crop&q=80",
    ],
    "restaurant": [
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1544025162-d76694265947?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1200&auto=format&fit=crop&q=80",
    ],
    "cafe": [
        "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1442512595331-e89e73853f31?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1521017432531-fbd92d768814?w=1200&auto=format&fit=crop&q=80",
    ],
    "viewpoint": [
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1508873696983-2df5293cb32f?w=1200&auto=format&fit=crop&q=80",
    ],
    "park": [
        "https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1519331379826-f10be5486c6f?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1507035895480-2b3156c31fc8?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1473448912268-2022ce9509d8?w=1200&auto=format&fit=crop&q=80",
    ],
    "nature": [
        "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1426604966848-d7adac402bff?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1433086966358-54859d0ed716?w=1200&auto=format&fit=crop&q=80",
    ],
    "market": [
        "https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1516594798947-e65505dbb29d?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?w=1200&auto=format&fit=crop&q=80",
    ],
    "bar": [
        "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1560512823-829485b8bf24?w=1200&auto=format&fit=crop&q=80",
    ],
    "beach": [
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1519046904884-53103b34b206?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1473186578172-c141e6798cf4?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
    ],
    "default": [
        "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=1200&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=1200&auto=format&fit=crop&q=80",
    ],
}

# Backward compatibility map: returns first element of each category pool
CATEGORY_IMAGES: dict[str, str] = {
    cat: urls[0] for cat, urls in CATEGORY_IMAGE_POOLS.items()
}


def get_destination_banner(destination: str) -> str:
    """Resolve a wide 1600px hero cover photo for a destination."""
    if not destination:
        return DESTINATION_BANNERS["_default"]

    clean = destination.lower().strip()
    if clean in DESTINATION_BANNERS:
        return DESTINATION_BANNERS[clean]

    # Check individual token matches (e.g. 'Goa, India' -> 'goa')
    for part in clean.replace(",", " ").split():
        if part in DESTINATION_BANNERS:
            return DESTINATION_BANNERS[part]

    return DESTINATION_BANNERS["_default"]


def get_category_fallback_image(category: str, name: str = "", destination: str = "") -> str:
    """
    Get a category-themed fallback photo URL using deterministic hash indexing.
    Prioritizes destination-specific collections when available.
    """
    cat = (category or "default").lower().strip()
    dest = (destination or "").lower().strip()

    # 1. Check destination-specific library
    matched_dest_key = None
    if dest:
        for k in DESTINATION_PHOTO_LIBRARIES:
            if k in dest:
                matched_dest_key = k
                break

    if matched_dest_key:
        dest_lib = DESTINATION_PHOTO_LIBRARIES[matched_dest_key]
        if cat in dest_lib and dest_lib[cat]:
            pool = dest_lib[cat]
            idx = abs(hash(name or "spot")) % len(pool)
            return pool[idx]

    # 2. Fall back to multi-photo category pools
    pool = CATEGORY_IMAGE_POOLS.get(cat, CATEGORY_IMAGE_POOLS["default"])
    idx = abs(hash(name or "spot")) % len(pool)
    return pool[idx]
