from sqlalchemy.orm import Session
from src.entity.match import Match  # noqa: F401
from src.entity.player import Player
from src.repository import player_repo
from src.service.scrapper import search_player, get_personal_details

def fill_player_details(session: Session, player_raw_name: str) -> Player:
    """
    """
    player = player_repo.find_player_by_name(db=session, name=player_raw_name)

    if player is not None:
        player_list = search_player(raw_name=player_raw_name)
        
        if player.tennis_id is None:
            if not player_list:
                raise ValueError(f"Player {player_raw_name} not found")
            elif player_list and len(player_list) == 1:
                player_data = player_list[0]
                player_repo.add_player_id(session, player, player_data.get("player_id"))
            else:
                # 'Herbert P.H.' => ['Pierre-Hugues Herbert', 'Pierre-Hugues Herbert']
                # The initials in the player name above are 'P.H.'
                # Find the player whose first name initials match the ones in the player_raw_name
                player_raw_name_parts = player_raw_name.split(' ')
                firstname_initials = player_raw_name_parts[-1]
                print(f"Player initials: {firstname_initials}")

                for player_data in player_list:
                    if player_first_name := player_data.get("first_name"):
                        print(f"Player first name: {player_first_name}")
                        player_name_parts = player_first_name.replace("-", " ").split(' ')
                        player_firstname_initials = ''.join(list(map(lambda x: f"{x[0]}.", player_name_parts)))

                        if firstname_initials == player_firstname_initials:
                            player_repo.add_player_id(session, player, player_data.get("player_id"))
                            break
                    else:
                        continue
                
                if player.tennis_id is None:
                    raise ValueError(f"Player {player_raw_name} not found")
        else:
            # Find the player in the list using playerId
            player_data = next((p for p in player_list if p.get("player_id") == player.tennis_id), None)
            if player_data is None:
                raise ValueError(f"Player {player_raw_name} not found")
                
        if player.tennis_id is not None and player.caracteristics is None:
            # Fetch player details using tennis_id
            caracs = get_personal_details(playerId=player_data.get("player_id"))
            player_repo.add_caracteristics(db=session, player=player, caracs=caracs)
    
    return player
