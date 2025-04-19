from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bs4 import BeautifulSoup
import requests
import json

app = FastAPI()

origins = [
    "http://localhost:3000",  # Example: Your local development frontend
    "https://your-other-app-domain.com",  # Replace with the actual domain of your other app
    "*",  # Be cautious with this in production; it allows all origins
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

SEARCH_URL = "https://minsante.cm/site/?q=fr/search/node/ambulance"
scraped_data = []  # In-memory storage for scraped data

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
    """
    Récupère et retourne les données relatives aux ambulances du site du Ministère de la Santé du Cameroun.
    Les données sont mises à jour à chaque requête.
    """
    global scraped_data
    scraped_data = scrape_search_results(SEARCH_URL)
    return JSONResponse(content=scraped_data)

@app.get("/update_ambulance_data")
async def update_ambulance_data():
    """
    Force la mise à jour des données relatives aux ambulances et les retourne.
    """
    global scraped_data
    scraped_data = scrape_search_results(SEARCH_URL)
    return JSONResponse(content=scraped_data)

@app.get("/")
async def read_root():
    """
    Point d'entrée de l'API. Fournit une description de l'API.
    """
    return {
        "message": "API pour récupérer les informations sur les ambulances du Ministère de la Santé du Cameroun.",
        "endpoints": {
            "/ambulance_data": "Récupère et retourne les données actuelles sur les ambulances.",
            "/update_ambulance_data": "Force la mise à jour et retourne les données sur les ambulances."
        }
    }
