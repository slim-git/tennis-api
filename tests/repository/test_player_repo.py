from src.repository.player_repo import (
    find_player_by_name,
    add_caracteristics,
    add_player_id,
)

def test_find_player_by_name(db_session, super_joueur):
    """
    Test finding a player by name
    """
    player_name = super_joueur.name
    player = find_player_by_name(db=db_session, name=player_name)

    assert player is not None
    assert player.name == player_name
    assert player.caracteristics is not None

def test_add_caracteristics(db_session, nouveau_joueur):
    """
    Test adding caracteristics to a player
    """
    caracteristics = {
        "first_name": "Nouveau",
        "last_name": "Joueur",
        "birth_date": "1995-01-01",
        "pro_year": 2015,
        "nationality": "France",
        "play_hand": "R",
        "back_hand": 1,
        "height_cm": 180,
        "weight_kg": 75,
    }

    assert nouveau_joueur.caracteristics is None
    caracs = add_caracteristics(db=db_session, player=nouveau_joueur, caracs=caracteristics)
    
    assert nouveau_joueur.caracteristics is not None
    assert nouveau_joueur.caracteristics == caracs
    assert nouveau_joueur.caracteristics.first_name == caracteristics.get('first_name')
    assert nouveau_joueur.caracteristics.last_name == caracteristics.get('last_name')
    assert nouveau_joueur.caracteristics.date_of_birth == caracteristics.get('birth_date')
    assert nouveau_joueur.caracteristics.pro_year == caracteristics.get('pro_year')
    assert nouveau_joueur.caracteristics.nationality == caracteristics.get('nationality')
    assert nouveau_joueur.caracteristics.play_hand == caracteristics.get('play_hand')
    assert nouveau_joueur.caracteristics.back_hand == caracteristics.get('back_hand')
    assert nouveau_joueur.caracteristics.height_cm == caracteristics.get('height_cm')
    assert nouveau_joueur.caracteristics.weight_kg == caracteristics.get('weight_kg')

def test_add_player_id(db_session, tout_nouveau_joueur):
    """
    Test adding a player id to a player
    """
    player_id = 'J003'
    
    assert tout_nouveau_joueur.tennis_id is None
    
    add_player_id(db=db_session, player=tout_nouveau_joueur, player_id=player_id)
    
    assert tout_nouveau_joueur.tennis_id == player_id