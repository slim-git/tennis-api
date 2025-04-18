import requests
from typing import List, Dict

def search_player(raw_name: str) -> List[Dict]:
    """
    Search for a player by name

    Example usage:
    import json
    name = 'Federer'
    players = search_player(name)
    print(json.dumps(players, indent=4))
    """
    last_name = " ".join(raw_name.split(" ")[:-1])

    # Construct the URL for the ATP Tour search
    url = f"https://www.atptour.com/en/-/www/site-search/{last_name}/"

    # Ajax request to fetch player data
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Uncomment the following lines to make an actual request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code}")
    
    # Parse the JSON response
    data = response.json()

    # Check if the response contains player data
    if 'Players' not in data or not data['Players']:
        raise Exception("No player data found")
    
    # Extract player data
    players = []
    for player in data['Players']:
        if last_name.lower() != player['LastName'].lower():
            continue

        player_data = {
            'name': f"{player['FirstName']} {player['LastName']}",
            'first_name': player['FirstName'],
            'last_name': player['LastName'],
            'country': player.get('NatlId'),
            'active': player.get('Active', 'I'),
            'headshot_url': player.get('PlayerHeadshotUrl'),
            'sub_category_name': player.get('SubCategoryName'),
            'player_id': player['PlayerId'],
        }
        players.append(player_data)
    
    return players

def get_personal_details(playerId: str) -> Dict:
    """
    Get personal details of a player

    Example usage:
    import json
    playerId = 'F324'  # Federer
    details = get_personal_details(playerId)
    print(json.dumps(output, indent=4))
    """
    # AJAX request to fetch player details
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Uncomment the following lines to make an actual request
    response = requests.get(f"https://www.atptour.com/en/-/www/players/hero/{playerId}", headers=headers)

    response.raise_for_status()
    
    data = response.json()

    # Extract personal details
    personal_details = {
        'last_name': data['LastName'],
        'first_name': data['FirstName'],
        'nationality': data['Nationality'],
        'birth_date': data['BirthDate'],
        'pro_year': data['ProYear'],
        'height_cm': data['HeightCm'],
        'weight_kg': data['WeightKg'],
        'play_hand': data['PlayHand']['Id'],
        'back_hand': data['BackHand']['Id'],
    }

    return personal_details