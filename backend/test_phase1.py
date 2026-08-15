import asyncio, json, httpx

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post('http://localhost:8000/plan', json={
            'session_id': 'test-phase1',
            'message': '3 days in Lisbon, hidden gems focus, budget 800 dollars'
        })
        data = resp.json()
        it = data.get('itinerary', {})
        days = it.get('days', [])
        dest = it.get('trip_request', {}).get('destination', '?')
        print(f"Status: {resp.status_code}")
        print(f"Destination: {dest}")
        print(f"Days: {len(days)}")
        for d in days:
            stops = d.get('stops', [])
            theme = d.get('theme', '')
            print(f"  Day {d['day_number']} ({theme!r}): {len(stops)} stops")
            for s in stops[:2]:
                print(f"    - {s['name']} [{s['category']}] ({s['lat']:.4f}, {s['lon']:.4f})")

asyncio.run(test())
