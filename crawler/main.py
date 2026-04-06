import requests, tqdm, json, time, os
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

'''
Dado o nome de um arquivo, carrega na memoria o conteudo de um .json dentro de um dicionario.
'''
def loadProgressDict(fileName):
    try:
        with open(fileName,'r',encoding='UTF-8') as file:
            progress = json.load(file)
            return progress
    except FileNotFoundError:
        return {}

'''
Dado o nome de um arquivo e um dicionario, salva as informações do dicionario como um .json
'''
def saveProgress(fileName:str,info):
    with open(fileName,'w',encoding='UTF-8') as file:
        json.dump(info,file, indent=4, ensure_ascii=False)


'''
Dado o id de um ator, tenta coletar as informações basicas
'''
def getInfoAtorElenco(href: str, session:requests.Session):
    try:
        with session.get('https://www.themoviedb.org'+href) as page:
            page.raise_for_status()
            html = page.text
            soup = BeautifulSoup(html, 'lxml')
            ator = {}

            nome = soup.find('h2',attrs={'class':"title"}).a.text
            ator['Nome'] = nome
            fatos = soup.find('section', attrs={'class':'facts'})

            for p in fatos.find_all('p'):
                if p.strong and p.bdi and not ("Também conhecido(a)" in p.get_text()):
                    label = p.strong.bdi.get_text(strip=True)
                    value = p.get_text(strip=True).replace(label, '').strip()
                    ator[label] = value
                pass
            return ator
    except (requests.exceptions.RequestException, Exception) as e:
        with open('LastLog.txt','w',encoding='UTF-8')as file:
            file.write('Erro ao realizar requisição para coleta de informações sobre elenco! Abortando para manter integridade.')
        exit()
    
'''
Dada um dicionario de filmografia, obtem a lista de atores que participaram de cada filme (sem repetição).
'''
def getCoestrelas(filmografia:dict,session:requests.Session):
    coEstrelas = loadProgressDict('Coestrelas.json')
    pbar_total = tqdm.tqdm(filmografia.values(), desc="Processando Filmografia", unit="filme")

    total_itens = len(pbar_total)
    delay_por_item = 1 / total_itens if total_itens > 0 else 0


    for filme in pbar_total:
        pbar_total.set_description(f"Filme: {filme['Nome']}")
        start_time = time.time()

        for ator in tqdm.tqdm(filme['Elenco'],desc=" > Elenco", leave=False, unit="ator"):
            if not coEstrelas.get(ator):
                info = getInfoAtorElenco(ator,session)
                coEstrelas[ator] = info
        saveProgress('Coestrelas.json',coEstrelas)

        tempo_decorrido = time.time() - start_time
        if tempo_decorrido < delay_por_item:
            time.sleep(delay_por_item - tempo_decorrido)
    return coEstrelas

'''
Dada a referência de uma filme, obtém o elenco (pode repetir)
'''
def getElenco(href:str, session:requests.Session):
    with session.get("https://www.themoviedb.org" + href + "/cast") as page:
        html = page.text
        soup = BeautifulSoup(html, 'lxml')
        castlist = soup.find('ol', attrs={'class': 'people credits'}).find_all('div', attrs={'class': 'info'})
        elenco = []

        for c in castlist:
            elenco.append(c.find_next('p').a['href'])
            pass

        return elenco

'''
Dada a referência de um filme, obtém informações sobre ele
"Diretor":      O diretor do filme
"Lançamento":   Data de Lançamento do filme (A depender da região)
"Duração":      A duração do filme
"Elenco":       Uma lista que contém a referencia dos atores que participaram do filme
'''
def getInfoFilme(href: str, session: requests.Session):
    url_completa = "https://www.themoviedb.org" + href
    try:
        with session.get(url_completa, timeout=15) as page:
            page.raise_for_status()

            html = page.text
            soup = BeautifulSoup(html, 'lxml')

            # extraindo generos
            generos = []
            divGen = soup.find('span', attrs={'class': 'genres'}).find_all('a')
            if divGen != None:
                for gen in divGen:
                    generos.append(gen.get_text().strip())
            else:
                generos = 'Não Especificado'

            # extraindo data de lançamento
            divLaunch = soup.find('span',attrs={"class":"release"})
            if divLaunch!= None:
                lancamento = divLaunch.get_text().strip()
            else:
                lancamento = 'Não Especificado'

            # extraindo duração
            divDur = soup.find('span',attrs={"class":"runtime"})
            if divDur!= None:
                duracao = divDur.get_text().strip()
            else:
                duracao = 'Não Especificado'

            # extraindo diretor
            divDir = soup.find('li', attrs={'class': 'profile'})
            if divDir and divDir.p:
                nome = divDir.p.getText(strip=True)
                Dhref = divDir.p.a['href'] if divDir.p.a else "N/A"
                diretor = (Dhref, nome)
            else:
                diretor = ("N/A", "Desconhecido")

            # extraindo o elenco
            elenco = getElenco(href, session)

            movieInfo = {'Genero': generos,
                         'Lançamento': lancamento,
                         'Diretor': diretor,
                         'Duracao': duracao,
                         'Elenco': elenco}
            return movieInfo

    except Exception as e:
        with open("erros_extracao.log", "a", encoding="utf-8") as log:
            log.write(f"ERRO: {href} | Motivo: {str(e)}\n")
        try:
            nome_arquivo = f"erro_{(href)}.html"
            if not os.path.exists("debug_errors"):
                os.makedirs("debug_errors")

            caminho_completo = os.path.join("debug_errors", nome_arquivo)

            with open(caminho_completo, "w", encoding="utf-8") as f:
                conteudo = page.text if 'page' in locals() else "Não foi possível baixar o HTML"
                f.write(f"\n")
                f.write(f"\n")
                f.write(conteudo)
        except:
            pass 
        return [], ("Erro", "Erro"), {}

'''
Dada uma pagina de um Ator, retorna a filmografia, contendo somente os filmes que
este ator fez parte, junto com informações sobre o filme
"href": {
    "Diretor":"",           Diretor do filme
    "Lançamento": "",       Data de lançamento do filme
    "Duração": "",          Duração do filme
    "Elenco": []            Uma lista de href que apontam para cada ator do elenco
}
'''
def getFilmografia(soup:BeautifulSoup, session: requests.Session):
    filmes = soup.find_all('a', attrs={'class':'tooltip'})
    saveName = 'Filmografia.json'

    filmeStack = loadProgressDict(saveName)
    total_itens = len(filmes)
    delay_por_item = 0.1 / total_itens if total_itens > 0 else 0

    for f in tqdm.tqdm(filmes,desc='Filmografia',leave=True):
        start_time = time.time()
        href = f['href']
        if not filmeStack.get(href):
            if "movie" in href:
                info = getInfoFilme(href,session)
                filmeStack[href] = {
                        "Nome":f.bdi.get_text().strip(),
                        'Genero': info['Genero'],
                        'Lançamento': info['Lançamento'],
                        'Diretor': info['Diretor'],
                        'Duracao': info['Duracao'],
                        'Elenco': info['Elenco']
                    }
                saveProgress(saveName,filmeStack)
        tempo_decorrido = time.time() - start_time
        if tempo_decorrido < delay_por_item:
            time.sleep(delay_por_item - tempo_decorrido)
    return filmeStack


'''
Dado o id do ator, retorne as informações basicas deste ator, filmes que trabalhou 
e colegas que teve ao longo da carreira.
'''
def getInfoAtorPrincipal(href: str, session:requests.Session):
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

    saveProgress("AtorPrincipal.json",ator)


    filmografia = getFilmografia(soup, session)
    
    print("Informações basicas e filmografia coletadas!")
    return ator,filmografia

'''
Cria uma request.Session, que será passada por entre as funções do crawler.
'''
def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Referer': 'https://www.themoviedb.org/'
    })
    # caso de threading
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('https://', adapter)
    return session

'''
Abra uma sessão para rodar as requisições.
'''
def start(href:str):
    with get_session() as session:
        ator, filmografia = getInfoAtorPrincipal(href,session)

        ator['Filmografa'] = filmografia

        saveProgress('Sir Lee.json',ator)

        colegasElenco = getCoestrelas(filmografia,session)
        ator['CoEstrelas'] = colegasElenco
        filename = ator['Nome'] + '.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(ator, f, indent=4, ensure_ascii=False)

# href, link da referencia para a pagina no TMDB (https://www.themoviedb.org/)
# Coloque no seguinte formato: '/person/{id}'
# Evite: 'person/113-christopher-lee' ; '/person/christopher-lee'

href = '/person/113-christopher-lee'
start(href)