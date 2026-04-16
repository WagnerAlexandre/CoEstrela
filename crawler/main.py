import requests
import pandas as pd
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
import tqdm
import json

def loadProgressDict(fileName):
    '''
    Dado o nome de um arquivo, carrega na memoria o conteudo de um .json dentro de um dicionario.
    '''
    try:
        with open(fileName,'r',encoding='UTF-8') as file:
            progress = json.load(file)
            return progress
    except FileNotFoundError:
        return {}

def saveProgress(fileName: str, info):
    '''
    Salva cada ator como uma linha independente no arquivo.
    '''
    with open(fileName, 'a', encoding='UTF-8') as file:
        line = json.dumps(info, ensure_ascii=False)
        file.write(line + '\n')

def getInfoAtor(href: str, session:requests.Session):
    '''
    Dado o id do ator, retorne as informações basicas deste ator, filmes que trabalhou 
    e colegas que teve ao longo da carreira.
    '''
    page = session.get('https://www.themoviedb.org'+href)
    html = page.text
    soup = BeautifulSoup(html, 'lxml')

    ator = {
        "Nome":"",
        "Conhecido(a) por":"",
        "Creditado(a) em":"",
        "Gênero":"",
        "Nascimento":"",
        "Falecimento":"",
        "Local de nascimento (em inglês)":""
    }

    nome = soup.find('h2',attrs={'class':"title"}).a.text
    ator['Nome'] = nome
    fatos = soup.find('section', attrs={'class':'facts'})

    for p in fatos.find_all('p'):
        if p.strong and p.bdi and not ("Também conhecido(a)" in p.get_text()):
            label = p.strong.bdi.get_text(strip=True)
            value = p.get_text(strip=True).replace(label, '').strip()
            ator[label] = value
        pass

    saveProgress("Atores.json",ator)

    
    print("Informações basicas coletadas!")
    return ator

def get_session():
    '''
    Cria uma request.Session, que será passada por entre as funções do crawler.
    '''
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Referer': 'https://www.themoviedb.org/'
    })
    # caso de threading
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('https://', adapter)
    return session

session = get_session()
with open('./dados/filtered_people.json','r',encoding='UTF-8') as file:
    df_ids = pd.read_json(file)
    for index, row in tqdm.tqdm(df_ids.iterrows()):
        person_id = row['id']
        nome_original = row['name']
    
    print(f"Coletando: {nome_original} (ID: {person_id})...")
    try:
        getInfoAtor(person_id, session)
    except Exception as e:
        print(f"Erro ao coletar ID {person_id}: {e}")