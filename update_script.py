import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import re
from collections import Counter

# Tradução manual dos meses para português
MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

def formatar_data_pt(dt):
    return f"{dt.day:02d} de {MESES_PT[dt.month]} de {dt.year}"

def extract_text_from_html(html_content):
    """Extrai texto puro do HTML de um artigo."""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove scripts, styles, etc.
    for script in soup(["script", "style", "header", "footer", "nav"]):
        script.extract()
    text = soup.get_text(separator=' ')
    # Limpa espaços extras
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_keywords(text, num_keywords=5):
    """Extrai palavras-chave do texto."""
    # Remove pontuação e converte para minúsculas
    text = re.sub(r'[^\w\s]', '', text.lower())
    
    # Remove stopwords em português
    stopwords = ["o", "a", "os", "as", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", 
                "no", "na", "nos", "nas", "ao", "aos", "à", "às", "pelo", "pela", "por", "para", 
                "em", "que", "com", "se", "não", "e", "é", "são", "mas", "ou"]
    
    words = [word for word in text.split() if word not in stopwords and len(word) > 3]
    
    # Conta frequência
    word_counts = Counter(words)
    
    # Retorna as mais frequentes
    return [word for word, _ in word_counts.most_common(num_keywords)]

def find_related_articles(article_id, article_data, num_related=3):
    """Encontra artigos relacionados baseados em tags e conteúdo."""
    target = article_data[article_id]
    scores = {}
    
    for id, data in article_data.items():
        if id == article_id:
            continue
        
        score = 0
        
        # Correspondência de tags (peso alto)
        common_tags = set(target['tags']).intersection(set(data['tags']))
        score += len(common_tags) * 3
        
        # Correspondência de categoria (peso médio)
        if target['category'] == data['category']:
            score += 2
        
        # Correspondência de palavras-chave (peso baixo)
        common_keywords = set(target['keywords']).intersection(set(data['keywords']))
        score += len(common_keywords)
        
        scores[id] = score
    
    # Ordena por pontuação e retorna os top N
    related = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:num_related]
    return [article_id for article_id, _ in related]

def get_article_metadata(file_path):
    """Extrai metadados completos de um arquivo HTML de artigo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # --- Extração de Metadados ---
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''

    # Extração de keywords (tags)
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    tags = []
    if meta_keywords and meta_keywords.get('content'):
        tags = [tag.strip() for tag in meta_keywords['content'].split(',')]
    
    # Busca por categoria de múltiplas formas
    meta_category = soup.find('meta', attrs={'name': 'category'})
    category = 'Tecnologia'  # Categoria padrão
    
    if meta_category and meta_category.get('content'):
        category = meta_category['content'].strip()
    else:
        # Tenta extrair da meta description ou do OG description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content') and 'Em ' in meta_desc['content']:
            category = meta_desc['content'].split('Em ')[1].split('.')[0]
        else:
            # Tenta extrair do artigo mesmo
            article_meta = soup.select('.article-meta a')
            for a in article_meta:
                if 'href' in a.attrs and '#' in a['href']:
                    category = a.text.strip()
                    break
            else:
                # Se tudo falhar, usa a primeira tag como categoria
                category = tags[0] if tags else 'Tecnologia'

    meta_author = soup.find('meta', attrs={'name': 'author'})
    author = 'IAUTOMATIZE'  # Autor padrão
    if meta_author and meta_author.get('content'):
        author = meta_author['content'].strip()
    
    meta_description = soup.find('meta', attrs={'name': 'description'})
    excerpt = ''
    if meta_description and meta_description.get('content'):
        excerpt = meta_description['content'].strip()

    meta_image = soup.find('meta', attrs={'property': 'og:image'})
    image_url = '../assets/images/articles/default.jpg'  # URL padrão
    if meta_image and meta_image.get('content'):
        image_url = meta_image['content'].strip()

    # Tenta extrair a data do JSON-LD, se existir
    publish_date = None
    script_ld = soup.find('script', attrs={'type': 'application/ld+json'})
    if script_ld:
        import json
        try:
            json_data = json.loads(script_ld.string)
            if 'datePublished' in json_data:
                publish_date = datetime.strptime(json_data['datePublished'], '%Y-%m-%d')
        except (json.JSONDecodeError, ValueError):
            pass
    
    # Se não conseguiu extrair a data, usa a data de modificação do arquivo
    if not publish_date:
        publish_date = datetime.fromtimestamp(os.path.getmtime(file_path))

    # Extrai texto para análise de palavras-chave
    text = extract_text_from_html(str(soup))
    keywords = extract_keywords(text)

    return {
        'title': title,
        'tags': tags,
        'category': category,
        'author': author,
        'excerpt': excerpt,
        'image_url': image_url,
        'publish_date': publish_date,
        'path': file_path.replace(os.path.sep, '/'),
        'keywords': keywords
    }

def add_breadcrumbs_to_article(file_path, metadata):
    """Adiciona breadcrumbs navegáveis ao artigo com base em seus metadados."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
        
        # Verificar se breadcrumbs já existem
        if soup.select('.breadcrumbs'):
            print(f"Breadcrumbs já existem em {file_path}")
            return
        
        # Obter informações para breadcrumbs
        title = metadata.get('title', 'Artigo')
        category = metadata.get('category', 'Geral')
        
        # Criar URL segura para a categoria
        safe_category = category.lower().replace(" ", "-")
        
        # Criar elemento breadcrumbs com parâmetro de URL para categoria
        breadcrumbs_html = f'''
        <nav aria-label="Breadcrumb" class="breadcrumbs">
          <div class="container">
            <ol itemscope itemtype="https://schema.org/BreadcrumbList">
              <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                <a itemprop="item" href="/">
                  <span itemprop="name">Home</span>
                </a>
                <meta itemprop="position" content="1" />
              </li>
              <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                <a itemprop="item" href="/?categoria={safe_category}">
                  <span itemprop="name">{category}</span>
                </a>
                <meta itemprop="position" content="2" />
              </li>
              <li itemprop="itemListElement" itemscope itemtype="https://schema.org/ListItem">
                <span itemprop="name">{title.split(" - ")[0].strip()}</span>
                <meta itemprop="position" content="3" />
              </li>
            </ol>
          </div>
        </nav>
        '''
        
        breadcrumbs_soup = BeautifulSoup(breadcrumbs_html, 'html.parser')
        
        # Inserir após o header e antes do main
        header = soup.find('header')
        main = soup.find('main')
        
        if header and main:
            # Inserir após o header
            header.insert_after(breadcrumbs_soup)
        elif main:
            # Se não encontrar header, inserir antes do main
            main.insert_before(breadcrumbs_soup)
        else:
            print(f"Não foi possível encontrar local para inserir breadcrumbs em {file_path}")
            return
        
        # Salvar o arquivo atualizado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"Breadcrumbs adicionados com sucesso em {file_path}")
        
    except Exception as e:
        print(f"Erro ao adicionar breadcrumbs em {file_path}: {str(e)}")

def add_related_articles_to_article(file_path, article_data, all_articles_data):
    """Adiciona artigos relacionados ao final do artigo."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
        
        # Obter o ID do artigo (nome do arquivo sem extensão)
        article_id = os.path.basename(file_path).replace('.html', '')
        
        # Encontrar artigos relacionados
        related_ids = find_related_articles(article_id, all_articles_data, num_related=3)
        
        # Encontrar a seção de artigos relacionados
        related_section = soup.find('section', id='related-articles')
        if not related_section:
            print(f"Seção de artigos relacionados não encontrada em {file_path}")
            return
        
        articles_grid = related_section.find('div', class_='articles-grid')
        if not articles_grid:
            print(f"Grid de artigos não encontrado em {file_path}")
            return
        
        # Limpar conteúdo existente
        articles_grid.clear()
        
        if not related_ids:
            # Se não há artigos relacionados, adicionar mensagem
            no_related_msg = soup.new_tag('p')
            no_related_msg.string = "Nenhum artigo relacionado encontrado no momento."
            no_related_msg.style = "text-align: center; color: #666; font-style: italic;"
            articles_grid.append(no_related_msg)
        else:
            # Adicionar artigos relacionados
            for related_id in related_ids:
                if related_id in all_articles_data:
                    related_article = all_articles_data[related_id]
                    
                    # Criar card do artigo relacionado
                    article_card = soup.new_tag('article', **{'class': 'article-card fade-in-on-scroll'})
                    
                    # Corrige URLs de imagem se necessário
                    image_url = related_article['image_url']
                    if not image_url.startswith(('http://', 'https://', '/')):
                        image_url = image_url if '../' in image_url else '../' + image_url
                    
                    # Criar HTML do card
                    card_html = f'''
                        <div class="article-image">
                            <a href="{related_article['path']}">
                                <img src="{image_url}" alt="{related_article['title']}" loading="lazy">
                            </a>
                        </div>
                        <div class="article-content">
                            <h3><a href="{related_article['path']}">{related_article['title']}</a></h3>
                            <p class="article-excerpt">{related_article['excerpt'][:150]}...</p>
                            <div class="article-meta">
                                <span>Por {related_article['author']}</span>
                                <time datetime="{related_article['publish_date'].strftime('%Y-%m-%d')}">
                                    {formatar_data_pt(related_article['publish_date'])}
                                </time>
                            </div>
                        </div>
                    '''
                    
                    article_card.append(BeautifulSoup(card_html, 'html.parser'))
                    articles_grid.append(article_card)
        
        # Salvar o arquivo atualizado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"Artigos relacionados adicionados com sucesso em {file_path}")
        
    except Exception as e:
        print(f"Erro ao adicionar artigos relacionados em {file_path}: {str(e)}")

def update_files():
    """Função principal para atualizar o index.html e sitemap.xml."""
    articles_dir = 'articles'
    all_articles_metadata = []
    all_articles_data = {}  # Para análise de artigos relacionados
    
    # Coleta metadados de todos os artigos
    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            try:
                metadata = get_article_metadata(file_path)
                all_articles_metadata.append(metadata)
                
                # Adicionar breadcrumbs ao artigo
                add_breadcrumbs_to_article(file_path, metadata)
                
                # Adicionar ao dicionário para análise de artigos relacionados
                article_id = filename.replace('.html', '')
                all_articles_data[article_id] = metadata
                
                print(f"Processado: {filename}")
            except Exception as e:
                print(f"Erro ao processar {filename}: {str(e)}")
    
    # Ordena todos os artigos por data de publicação (mais recentes primeiro)
    all_articles_metadata.sort(key=lambda x: x['publish_date'], reverse=True)

    # Adicionar artigos relacionados a cada artigo
    print("\n=== Adicionando artigos relacionados ===")
    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            add_related_articles_to_article(file_path, all_articles_data, all_articles_data)

    # --- Atualiza o index.html ---
    try:
        with open('index.html', 'r+', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')

            # --- Popula a seção de "Últimas Notícias" ---
            recent_articles_container = soup.find(id='recent-articles-container')
            if recent_articles_container:
                recent_articles_container.clear() # Limpa a área
                
                # Pega os artigos dos últimos 3 dias (ou os 3 mais recentes, se menos de 3 disponíveis)
                tres_dias_atras = datetime.now() - timedelta(days=3)
                artigos_recentes = [a for a in all_articles_metadata if a['publish_date'] >= tres_dias_atras]
                if len(artigos_recentes) < 3:
                    artigos_recentes = all_articles_metadata[:3]  # Garante pelo menos 3 cards
                
                for article in artigos_recentes:
                    date_str = formatar_data_pt(article['publish_date'])
                    category = article['category']
                    
                    # Criar URL segura para a categoria
                    safe_category = category.lower().replace(" ", "-")
                    
                    # Adicionar data-category ao card
                    article_card = soup.new_tag('article', **{
                        'class': 'article-card fade-in-on-scroll', 
                        'data-category': safe_category
                    })
                    
                    # Corrige URLs de imagem se necessário
                    image_url = article['image_url']
                    if not image_url.startswith(('http://', 'https://', '/')):
                        image_url = image_url if '../' in image_url else '../' + image_url
                    
                    article_card.append(BeautifulSoup(f'''
                        <div class="article-image">
                            <a href="{article['path']}"><img src="{image_url}" alt="{article['title']}" loading="lazy"></a>
                        </div>
                        <div class="article-content">
                            <h3><a href="{article['path']}">{article['title']}</a></h3>
                            <p class="article-excerpt">{article['excerpt']}</p>
                            <div class="article-meta">
                                <span>Por {article['author']}</span>
                                <time datetime="{article['publish_date'].strftime('%Y-%m-%d')}">{date_str}</time>
                                <span class="article-category">Em <a href="/?categoria={safe_category}">{category}</a></span>
                            </div>
                        </div>
                    ''', 'html.parser'))
                    
                    recent_articles_container.append(article_card)
                
                print(f"Adicionados {len(artigos_recentes)} artigos à seção de últimas notícias")

            # Popula a seção de Categorias
            categories_container = soup.find(id='categories-container')
            if categories_container:
                categories_container.clear()
                all_categories = sorted(list(set(article['category'] for article in all_articles_metadata if article['category'])))
                for category in all_categories:
                    # Criar URL segura para a categoria
                    safe_category = category.lower().replace(" ", "-")
                    
                    card = soup.new_tag('div', **{'class': 'category-card fade-in-on-scroll'})
                    card.append(BeautifulSoup(f'''<a href="/?categoria={safe_category}" class="category-link"><i class="fas fa-robot"></i><h3>{category}</h3><p>Artigos sobre {category}</p></a>''', 'html.parser'))
                    categories_container.append(card)
                print(f"Adicionadas {len(all_categories)} categorias")

            # Popula a seção de Tags
            tags_container = soup.find(id='tags-container')
            if tags_container:
                tags_container.clear()
                all_tags = sorted(list(set(tag for article in all_articles_metadata for tag in article['tags'])))
                for tag in all_tags:
                    # Criar URL segura para a tag
                    safe_tag = tag.lower().replace(" ", "-")
                    tag_link = soup.new_tag('a', href=f'/?tag={safe_tag}', **{'class': 'tag-link'})
                    tag_link.string = tag
                    tags_container.append(tag_link)
                print(f"Adicionadas {len(all_tags)} tags")
            
            f.seek(0)
            f.write(str(soup.prettify(formatter='html5')))
            f.truncate()
            
    except Exception as e:
        print(f"Erro ao atualizar index.html: {str(e)}")

    # --- Atualiza o sitemap.xml ---
    sitemap_path = 'config/sitemap.xml'
    try:
        if os.path.exists(sitemap_path) and os.path.getsize(sitemap_path) > 10:
            with open(sitemap_path, 'r', encoding='utf-8') as f:
                sitemap_content = f.read()
                try:
                    sitemap_soup = BeautifulSoup(sitemap_content, 'xml')
                    if not sitemap_soup.find('urlset'):
                        raise ValueError("Sitemap não contém elemento urlset")
                except Exception:
                    # Se o parsing falhar, cria um novo sitemap
                    sitemap_soup = BeautifulSoup('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', 'xml')
        else:
            # Cria um novo sitemap
            sitemap_soup = BeautifulSoup('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>', 'xml')
            
        existing_urls = [loc.text for loc in sitemap_soup.find_all('loc')]
        urlset = sitemap_soup.find('urlset')

        # Domínio do blog - IMPORTANTE: ALTERE PARA SEU DOMÍNIO REAL
        domain = "https://blog.iautomatize.com"  # Substitua pelo seu domínio real
        
        # Adiciona a URL da página inicial
        if domain not in existing_urls:
            url_element = sitemap_soup.new_tag('url')
            loc_element = sitemap_soup.new_tag('loc')
            loc_element.string = domain
            lastmod_element = sitemap_soup.new_tag('lastmod')
            lastmod_element.string = datetime.now().strftime('%Y-%m-%d')
            url_element.append(loc_element)
            url_element.append(lastmod_element)
            urlset.append(url_element)

        # Adiciona URLs dos artigos
        for article in all_articles_metadata:
            # Formata a URL corretamente
            article_path = article['path'].replace('\\', '/')
            url = f"{domain}/{article_path}"
            
            if url not in existing_urls:
                url_element = sitemap_soup.new_tag('url')
                
                loc_element = sitemap_soup.new_tag('loc')
                loc_element.string = url
                url_element.append(loc_element)
                
                lastmod_element = sitemap_soup.new_tag('lastmod')
                lastmod_element.string = article['publish_date'].strftime('%Y-%m-%d')
                url_element.append(lastmod_element)
                
                urlset.append(url_element)
        
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write(str(sitemap_soup.prettify()))
        print(f"Sitemap atualizado com {len(sitemap_soup.find_all('url'))} URLs")
            
    except Exception as e:
        print(f"Erro ao atualizar sitemap.xml: {str(e)}")

if __name__ == '__main__':
    update_files()
