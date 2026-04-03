import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
import tqdm
import json
import os
import re


'''tabela de consulta rapida, trate como uma
cache para evitar acesso desnecessario para
uma pagina de um colega de elenco.
'''
global tableGender
tableGender = {}

'''
Dado a referencia de um participante do elenco, retorna o genero
'''
def getInfoCastGender(href: str, session:requests.Session):
    global tableGender

    if href in tableGender:
        return tableGender[href]
    else:
        url = "https://www.themoviedb.org" + href
        with session.get(url) as page:

            print(f"[GET] {url} -> Status: {page.status_code}")

            if page.status_code != 200:
                print(f"[ERRO HTTP] Falha ao acessar {url}")
                return None

            html = page.text
            soup = BeautifulSoup(html, 'lxml')

            fatos = soup.find('section', attrs={'class': 'facts'})


            if not fatos:
                print(f"[ERRO HTML] 'facts' não encontrado em {url}")
                return None

            for p in fatos.find_all('p'):
                if 'Gênero' in p.get_text():
                    label = p.strong.bdi.get_text(strip=True)
                    value = p.get_text(strip=True).replace(label, '').strip()
                    tableGender[href] = value
                    return value

            print(f"[INFO] Gênero não encontrado em {url}")
            return None


'''
Dado o id de um filme, coleta as informações do elenco (nome, referencia e genero)
'''
def getInfoCast(href: str, session: requests.Session):
    with session.get("https://www.themoviedb.org" + href + "/cast") as page:
        html = page.text
        soup = BeautifulSoup(html, 'lxml')

        castlist = soup.find('ol', attrs={'class': 'people credits'}).find_all('div', attrs={'class': 'info'})
        castRefer = {}
        for c in castlist:
            nome = c.a.getText()
            actor_href = c.a['href']
      
            genero = getInfoCastGender(actor_href, session)
            castRefer[actor_href] = {
                'nome': nome,
                'Genero': genero
            }
        return castRefer


def limpar_nome_arquivo(href):
    return re.sub(r'[\\/*?:"<>|]', "_", href.strip('/'))

def getInfoFilme(href: str, session: requests.Session):
    url_completa = "https://www.themoviedb.org" + href
    try:
        with session.get(url_completa, timeout=15) as page:
            # Se o status não for 200, lançamos um erro para cair no except
            page.raise_for_status()

            html = page.text
            soup = BeautifulSoup(html, 'lxml')

            # --- Extração de Gêneros ---
            divGen = soup.find_all('span', attrs={'class': 'genres'})
            generos = [g.getText(strip=True) for g in divGen]

            # --- Extração de Diretor ---
            # Usando find com proteção para caso o elemento não exista (evita AttributeError)
            divDir = soup.find('li', attrs={'class': 'profile'})
            if divDir and divDir.p:
                nome = divDir.p.getText(strip=True)
                Dhref = divDir.p.a['href'] if divDir.p.a else "N/A"
                diretor = (Dhref, nome)
            else:
                diretor = ("N/A", "Desconhecido")

            # --- Extração de Elenco ---
            elenco = getInfoCast(href, session)

            return generos, diretor, elenco

    except Exception as e:
        # 1. Registrar o erro no log
        with open("erros_extracao.log", "a", encoding="utf-8") as log:
            log.write(f"ERRO: {href} | Motivo: {str(e)}\n")

        # 2. Salvar o HTML da página que deu erro para análise posterior
        try:
            nome_arquivo = f"erro_{limpar_nome_arquivo(href)}.html"
            # Cria uma pasta de erros se não existir
            if not os.path.exists("debug_errors"):
                os.makedirs("debug_errors")

            caminho_completo = os.path.join("debug_errors", nome_arquivo)

            with open(caminho_completo, "w", encoding="utf-8") as f:
                # Tenta salvar o texto da página se ela chegou a ser baixada
                conteudo = page.text if 'page' in locals() else "Não foi possível baixar o HTML"
                f.write(f"\n")
                f.write(f"\n")
                f.write(conteudo)
        except:
            pass # Se falhar ao salvar o log de erro, apenas ignora para não travar o loop

        # Retorna valores vazios para que o loop principal continue sem quebrar
        return [], ("Erro", "Erro"), {}
'''
Dado o id de um ator, retorne as informações basicas deste ator, filmes que trabalhou.
'''
def getInfoAtor(href: str, session:requests.Session):
    page = session.get('https://www.themoviedb.org/'+href)
    html = page.text
    soup = BeautifulSoup(html, 'lxml')
    global tableGender

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
    if not tableGender.get(href):
        tableGender[href]=ator['Gênero']

    filmes = soup.find_all('a', attrs={'class':'tooltip'})
    filmeStack = []
    for f in filmes:
        filmeFormat = {
        "Nome": f.bdi.getText(),
        "href": f.get('href'),
        }

        filmeStack.append(filmeFormat)

    print("Informações basicas e filmografia coletadas!")
    return ator,filmeStack

'''
Remove entradas duplicadas de uma lista.
'''
def rmvDuplicatas(lista):
    vistos = set()
    nova_lista = []
    for filme in lista:
        if filme['href'] not in vistos:
            vistos.add(filme['href'])
            nova_lista.append(filme)
    return nova_lista

def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
        'Accept-Language': 'pt-BR,pt;q=0.9',
        'Referer': 'https://www.themoviedb.org/'
    })
    # Configurando o Pool para ser maior que o número de threads
    adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
    session.mount('https://', adapter)
    return session

'''
Abra uma sessão para rodar as requisições
'''
with get_session() as session:
    ator, filmes = getInfoAtor('person/113-christopher-lee',session)

    filmes = rmvDuplicatas(filmes)
    ator['Filmografa'] = filmes


    with open('Sir Lee.json', 'w', encoding='utf-8') as f:
        json.dump(ator, f, indent=4, ensure_ascii=False)

    colegasElenco = []
    with open('Sir LeeCowork.json', 'w', encoding='utf-8') as f:
        for filme in tqdm.tqdm(filmes, desc="Filmes analisados", position=1):
            generos,diretor,elenco = getInfoFilme(filme['href'],session)
            json.dump((generos,diretor,elenco), f, indent=4, ensure_ascii=False)
