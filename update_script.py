import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Tradução manual dos meses para português
MESES_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
]

def formatar_data_pt(dt):
    return f"{dt.day:02d} de {MESES_PT[dt.month]} de {dt.year}"

def get_article_metadata(file_path):
    """Extrai metadados completos de um arquivo HTML de artigo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # --- Extração de Metadados ---
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''

    # Extração de keywords (tags)
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    tags = [tag.strip() for tag in meta_keywords['content'].split(',')] if meta_keywords and meta_keywords.get('content') else []
    
    # Busca por categoria de múltiplas formas
    meta_category = soup.find('meta', attrs={'name': 'category'})
    if not meta_category or not meta_category.get('content'):
        # Tenta extrair da meta description ou do OG description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and 'Em ' in meta_desc.get('content', ''):
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
    else:
        category = meta_category['content'].strip()

    meta_author = soup.find('meta', attrs={'name': 'author'})
    author = meta_author['content'].strip() if meta_author and meta_author.get('content') else 'IAUTOMATIZE'
    
    meta_description = soup.find('meta', attrs={'name': 'description'})
    excerpt = meta_description['content'].strip() if meta_description and meta_description.get('content') else ''

    meta_image = soup.find('meta', attrs={'property': 'og:image'})
    image_url = meta_image['content'].strip() if meta_image and meta_image.get('content') else '../assets/images/articles/default.jpg'

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

    return {
        'title': title,
        'tags': tags,
        'category': category,
        'author': author,
        'excerpt': excerpt,
        'image_url': image_url,
        'publish_date': publish_date,
        'path': file_path.replace(os.path.sep, '/')
    }

def update_files():
    """Função principal para atualizar o index.html e sitemap.xml."""
    articles_dir = 'articles'
    all_articles_metadata = []
    
    # Coleta metadados de todos os artigos
    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            try:
                all_articles_metadata.append(get_article_metadata(file_path))
                print(f"Processado: {filename}")
            except Exception as e:
                print(f"Erro ao processar {filename}: {str(e)}")
    
    # Ordena todos os artigos por data de publicação (mais recentes primeiro)
    all_articles_metadata.sort(key=lambda x: x['publish_date'], reverse=True)

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
                    
                    # Corrige URLs de imagem se necessário
                    image_url = article['image_url']
                    if not image_url.startswith(('http://', 'https://', '/')):
                        image_url = '../' + image_url if '../' not in image_url else image_url
                    
                    # Cria o card do artigo
                    article_card = soup.new_tag('article', **{'class': 'article-card fade-in-on-scroll'})
                    
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
                    card = soup.new_tag('div', **{'class': 'category-card fade-in-on-scroll'})
                    card.append(BeautifulSoup(f'''<a href="#" class="category-link"><i class="fas fa-robot"></i><h3>{category}</h3><p>Artigos sobre {category}</p></a>''', 'html.parser'))
                    categories_container.append(card)
                print(f"Adicionadas {len(all_categories)} categorias")

            # Popula a seção de Tags
            tags_container = soup.find(id='tags-container')
            if tags_container:
                tags_container.clear()
                all_tags = sorted(list(set(tag for article in all_articles_metadata for tag in article['tags'])))
                for tag in all_tags:
                    tag_link = soup.new_tag('a', href=f'#', **{'class': 'tag-link'})
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
