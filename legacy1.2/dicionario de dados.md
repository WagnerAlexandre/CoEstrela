# 📋 Dicionário de Dados - Entidade Artista

Este dicionário descreve a estrutura JSON para armazenamento de informações biográficas, filmografia e conexões de artistas (co-estrelas).

---

## 1. Estrutura Raiz (Root)
Representa o perfil principal do artista consultado no banco de dados.

| Atributo | Tipo de Dado | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| **Nome** | `string` | Nome completo do artista principal. | "Christopher Lee" |
| **Conhecido(a) por** | `string` | Função principal na indústria (Atuação, Direção, etc). | "Atuação" |
| **Creditado(a) em** | `string` | Total de obras em que o nome aparece nos créditos. | "374" |
| **Gênero** | `string` | Identificação de gênero do artista. | "Masculino" |
| **Nascimento** | `string` | Data de nascimento (pode incluir a idade atual). | "27 de maio de 1922" |
| **Falecimento** | `string` | Data de falecimento e idade ao morrer (se houver). | "7 de junho de 2015" |
| **Local de nascimento** | `string` | Cidade, estado e país de origem (em inglês). | "Westminster, London" |
| **Filmografia** | `object` | Dicionário de objetos contendo as obras vinculadas. | `{...}` |
| **CoEstrelas** | `object` | Dicionário de objetos contendo pessoas relacionadas. | `{...}` |

---

## 2. Objeto: Filmografia
Contém as obras ligadas ao artista. A **Chave** do objeto é o `href` (ID único/URL da obra).

| Atributo Interno | Tipo de Dado | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| **Nome** | `string` | Título oficial da obra. | "The Lost Ending" |
| **Genero** | `array` | Lista de strings com os gêneros da obra. | `[Ação, Terror]` |
| **Lançamento** | `string` | Ano de estreia ou status de lançamento. | "21/11/2025 (GB)" |
| **Diretor** | `array` | Lista contendo o `href` e o `Nome` do diretor. | `["/person/152183", "Justin Hardy"]` |

---

## 3. Objeto: CoEstrelas
Contém perfis resumidos de colegas de trabalho. A **Chave** do objeto é o `href` (ID único/URL da pessoa).

| Atributo Interno | Tipo de Dado | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| **Nome** | `string` | Nome completo da co-estrela. | "Tim Plester" |
| **Conhecido(a) por** | `string` | Função principal da co-estrela. | "Atuação" |
| **Creditado(a) em** | `string` | Total de créditos da co-estrela na base. | "85" |
| **Gênero** | `string` | Identificação de gênero. | "Masculino" |
| **Nascimento** | `string` | Data de nascimento e idade. | "10 de setembro de 1970" |
| **Local de nascimento** | `string` | Cidade e país de origem da co-estrela. | "Banbury, England" |

