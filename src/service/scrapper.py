from typing import List, Dict
import requests
import json
import os
import re
from dotenv import load_dotenv
import logging
from starlette.status import HTTP_200_OK

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def get_without_flaresolverr(url: str) -> str:
    """
    Bypass Cloudflare protection using a standard request.
    This function sends a request to the given URL and returns the response content.
    """
    # Define request parameters
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Send request to the URL
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != HTTP_200_OK:
        raise Exception(f"Failed to fetch data: {response.status_code}")
    
    # Parse and return the JSON response
    return response.json()

def get_with_flaresolverr(url: str, flare_api: str) -> str:
    """
    Bypass Cloudflare protection using a dedicated service like FlareSolverr.
    This function sends a request to FlareSolverr and returns the response content.
    """
    # Define request parameters
    data = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }

    # Send request to FlareSolverr
    endpoint = flare_api + 'v1'
    response = requests.post(endpoint,
                             headers={"Content-Type": "application/json"},
                             json=data)
    
    response.raise_for_status()  # Raise an error for bad responses

    # Extract page content
    page_content = response.json().get('solution', {}).get('response', '')

    # Parse the HTML to extract the JSON inside <pre>
    match = re.search(r"<pre.*?>(.*?)</pre>", page_content, re.DOTALL)
    if match:
        json_text = match.group(1).strip()
        try:
            return json.loads(json_text)
        except json.JSONDecodeError:
            logger.error("Invalid JSON", json_text)
            raise
    else:
        raise ValueError("No <pre> tag found in the response")

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
    url = f"https://www.atptour.com/en/-/www/site-search/{last_name.lower()}/"

    if FLARESOLVERR_API := os.getenv("FLARESOLVERR_API"):
        # Use FlareSolverr to bypass Cloudflare
        data = get_with_flaresolverr(url=url, flare_api=FLARESOLVERR_API)
    else:
        data = get_without_flaresolverr(url)

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
    url = f"https://www.atptour.com/en/-/www/players/hero/{playerId}/"

    if FLARESOLVERR_API := os.getenv("FLARESOLVERR_API"):
        # Use FlareSolverr to bypass Cloudflare
        data = get_with_flaresolverr(url=url, flare_api=FLARESOLVERR_API)
    else:
        data = get_without_flaresolverr(url)

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