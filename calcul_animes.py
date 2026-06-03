import requests
from datetime import datetime, timedelta
from ics import Calendar, Event

# =======================================================
# CONFIGURATION : REMPLACEZ PAR VOTRE PSEUDO ENTRE LES ""
USER_NAME = "Elpadredelavega"
# =======================================================

URL = 'https://graphql.anilist.co'

query = '''
query ($username: String) {
  MediaListCollection(userName: $username, type: ANIME, status: PLANNING) {
    lists {
      entries {
        media {
          title {
            romaji
            english
          }
          episodes
          nextAiringEpisode {
            episode
            airingAt
          }
        }
      }
    }
  }
}
'''

variables = {'username': USER_NAME}

try:
    response = requests.post(URL, json={'query': query, 'variables': variables})
    data = response.json()

    if 'errors' in data:
        print(f"Erreur d'AniList : {data['errors'][0]['message']}")
        exit()

    if not data['data']['MediaListCollection']['lists']:
        print(f"Aucune liste 'Planned to watch' trouvée pour {USER_NAME} ou la liste est vide.")
        exit()

    lists = data['data']['MediaListCollection']['lists']
    
    cal = Calendar()
    animes_trouves = 0

    print(f"Analyse de la liste 'Planned to watch' de {USER_NAME}...\n")

    for l in lists:
        for entry in l['entries']:
            media = entry['media']
            title = media['title']['english'] or media['title']['romaji']
            total_episodes = media['episodes']
            next_airing = media['nextAiringEpisode']

            if next_airing:
                next_ep_num = next_airing['episode']
                next_ep_time = next_airing['airingAt']
                
                next_ep_date = datetime.fromtimestamp(next_ep_time)

                if total_episodes:
                    episodes_remaining = total_episodes - next_ep_num
                    days_to_add = episodes_remaining * 7
                    end_date = next_ep_date + timedelta(days=days_to_add)
                    
                    event = Event()
                    event.name = f"{title}"
                    # Correction de la date pour le format ICS standard
                    event.begin = end_date
                    event.make_all_day()
                    event.description = f"Dernier épisode ({total_episodes}) théorique calculé le {end_date.strftime('%d/%m/%Y')}."
                    
                    cal.events.add(event)
                    animes_trouves += 1
                    print(f"✔ {title} -> Fin estimée le {end_date.strftime('%d/%m/%Y')} (Épisode {total_episodes})")
                else:
                    print(f"⚠ {title} -> Nombre total d'épisodes inconnu, impossible de calculer la fin.")

    if animes_trouves > 0:
        filename = "fin_animes_planning_proton.ics"
        # CORRECTION CRITIQUE : l'argument newline='' empêche Windows de corrompre le fichier
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            f.write(cal.serialize())
        print(f"\nSuccès ! Le fichier '{filename}' a été créé avec {animes_trouves} événements.")
        print("Vous pouvez maintenant l'importer dans Proton Calendar.")
    else:
        print("\nAucun animé actuellement en cours de diffusion n'a été trouvé.")

except Exception as e:
    print(f"Une erreur est survenue : {e}")
