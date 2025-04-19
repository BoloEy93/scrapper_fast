from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from bs4 import BeautifulSoup
import requests
import json


app = FastAPI()

origins = ["*"]  # Adjust this for production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

faq_data = {
    "comment accéder au menu ambulance ?": "Le menu ambulance est généralement situé en haut de l'écran principal ou dans le menu de navigation (souvent une icône avec trois lignes). Cliquez dessus pour y accéder.",
    "que puis-je faire dans le menu ambulance ?": "Dans le menu ambulance, vous pouvez généralement consulter les informations sur les services d'ambulance, les contacts d'urgence, les procédures à suivre en cas d'urgence, et potentiellement localiser les ambulances à proximité.",
    "comment trouver les numéros d'urgence ?": "Les numéros d'urgence sont souvent affichés en évidence dans le menu ambulance, parfois dans une section dédiée 'Urgences' ou 'Contacts utiles'.",
    "où puis-je trouver de l'aide pour utiliser le menu ?": "Si vous avez besoin d'aide, consultez la section 'Aide' ou 'Instructions' dans le menu ambulance. Vous pouvez également contacter le support client si disponible.",
    "y a-t-il une carte des ambulances disponibles ?": "La disponibilité d'une carte des ambulances dépend de l'application. Vérifiez si une option 'Localisation des ambulances' ou 'Carte' est présente dans le menu.",
    "comment signaler une urgence via l'application ?": "Pour signaler une urgence, recherchez un bouton 'Signaler une urgence' ou une fonctionnalité similaire dans le menu ambulance. Suivez les instructions à l'écran pour fournir les informations nécessaires.",
}

initial_options = [
    {"title": "Comment accéder au menu ?", "payload": "comment accéder au menu ambulance ?"},
    {"title": "Que faire dans le menu ?", "payload": "que puis-je faire dans le menu ambulance ?"},
    {"title": "Où trouver les urgences ?", "payload": "comment trouver les numéros d'urgence ?"},
    {"title": "Besoin d'aide ?", "payload": "où puis-je trouver de l'aide pour utiliser le menu ?"},
    {"title": "Carte des ambulances ?", "payload": "y a-t-il une carte des ambulances disponibles ?"},
    {"title": "Signaler une urgence", "payload": "comment signaler une urgence via l'application ?"},
]

class ChatbotRequest(BaseModel):
    message: str

class ChatbotResponse(BaseModel):
    response: str
    options: Optional[List[dict]] = None

@app.get("/chatbot/start")
async def chatbot_start():
    return ChatbotResponse(
        response="Bonjour ! Comment puis-je vous aider aujourd'hui concernant le menu ambulance ?",
        options=initial_options
    )

@app.post("/chatbot")
async def chatbot_endpoint(request: ChatbotRequest):
    user_message = request.message.lower().strip()
    if user_message in faq_data:
        return ChatbotResponse(response=faq_data[user_message])
    else:
        return ChatbotResponse(
            response="Je ne suis pas sûr de comprendre votre question. Voici quelques options :",
            options=initial_options
        )

# --- Dummy scraping endpoints (keep these for completeness) ---
SEARCH_URL = "https://minsante.cm/site/?q=fr/search/node/ambulance"
scraped_data = []

def scrape_search_results(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        search_results_ol = soup.select_one('ol.search-results.node-results')
        results_data = []

        if search_results_ol:
            list_items = search_results_ol.find_all('li')
            for item in list_items:
                title_element = item.select_one('h3.title a')
                snippet_element = item.select_one('div.search-snippet-info p.search-snippet')
                info_element = item.select_one('div.search-snippet-info p.search-info')

                title = title_element.text.strip() if title_element else None
                link = "https://minsante.cm" + title_element['href'] if title_element and 'href' in title_element.attrs else None
                snippet = snippet_element.text.strip() if snippet_element else None
                info = info_element.text.strip() if info_element else None

                result_item = {
                    "title": title,
                    "link": link,
                    "snippet": snippet,
                    "info": info
                }
                results_data.append(result_item)
        else:
            raise HTTPException(status_code=500, detail="Impossible de trouver la liste des résultats de recherche sur la page.")

        return results_data

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur de connexion au site du Ministère de la Santé: {e}")
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=response.status_code, detail=f"Erreur HTTP lors de la récupération de la page: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur inattendue s'est produite: {e}")

@app.get("/ambulance_data")
async def get_ambulance_data():
    global scraped_data
    scraped_data = scrape_search_results(SEARCH_URL)
    return JSONResponse(content=scraped_data)

@app.get("/update_ambulance_data")
async def update_ambulance_data():
    global scraped_data
    scraped_data = scrape_search_results(SEARCH_URL)
    return JSONResponse(content=scraped_data)

@app.get("/")
async def read_root():
    return {
        "message": "API pour récupérer les informations sur les ambulances du Ministère de la Santé du Cameroun.",
        "endpoints": {
            "/ambulance_data": "Récupère et retourne les données actuelles sur les ambulances.",
            "/update_ambulance_data": "Force la mise à jour et retourne les données sur les ambulances.",
            "/chatbot/start": "Endpoint pour démarrer l'interaction avec le chatbot.",
            "/chatbot": "Endpoint pour envoyer un message au chatbot."
        }
    }
