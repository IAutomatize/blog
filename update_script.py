import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def get_article_metadata(file_path):
    """Extrai metadados (título, tags, categoria) de um arquivo HTML de artigo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''

    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    tags = [tag.strip() for tag in meta_keywords['content'].split(',')] if meta_keywords and meta_keywords.get('content') else []
    
    meta_category = soup.find('meta', attrs={'name': 'category'})
    category = meta_category['content'].strip() if meta_category and meta_category.get('content') else ''

    return {
        'title': title,
        'tags': tags,
        'category': category,
        'path': file_path.replace(os.path.sep, '/')
    }

def update_files():
    """Função principal para atualizar o index.html e sitemap.xml."""
    articles_dir = 'articles'
    recent_articles_metadata = []
    three_days_ago = datetime.now() - timedelta(days=3)

    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            # Coleta metadados de todos os artigos para popular tags e categorias, não apenas os recentes
            recent_articles_metadata.append(get_article_metadata(file_path))

    # --- Atualiza o index.html ---
    with open('index.html', 'r+', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

        # Popula a seção de Categorias
        categories_container = soup.find(id='categories-container')
        if categories_container:
            categories_container.clear()
            all_categories = sorted(list(set(article['category'] for article in recent_articles_metadata if article['category'])))
            
            for category in all_categories:
                card = soup.new_tag('div', **{'class': 'category-card fade-in-on-scroll'})
                icon = soup.new_tag('i', **{'class': 'fas fa-robot'}) # Ícone padrão
                title = soup.new_tag('h3')
                title.string = category
                desc = soup.new_tag('p')
                desc.string = f"Artigos sobre {category}"
                card.extend([icon, title, desc])
                categories_container.append(card)

        # Popula a seção de Tags
        tags_container = soup.find(id='tags-container')
        if tags_container:
            tags_container.clear()
            all_tags = sorted(list(set(tag for article in recent_articles_metadata for tag in article['tags'])))
            
            for tag in all_tags:
                tag_link = soup.new_tag('a', href=f'#', **{'class': 'tag-link'}) # Placeholder link
                tag_link.string = tag
                tags_container.append(tag_link)
        
        f.seek(0)
        f.write(str(soup.prettify(formatter='html5')))
        f.truncate()

    # --- Atualiza o sitemap.xml ---
    sitemap_path = 'sitemap.xml'
    if os.path.exists(sitemap_path):
        with open(sitemap_path, 'r+', encoding='utf-8') as f:
            sitemap_soup = BeautifulSoup(f.read(), 'xml')
            
            existing_urls = [loc.text for loc in sitemap_soup.find_all('loc')]
            urlset = sitemap_soup.find('urlset')

            if urlset:
                for article in recent_articles_metadata:
                    # Garante que a URL base esteja correta
                    url = f"https://iautomatize.github.io/blog/{article['path']}"
                    if url not in existing_urls:
                        url_element = sitemap_soup.new_tag('url')
                        loc_element = sitemap_soup.new_tag('loc')
                        loc_element.string = url
                        url_element.append(loc_element)
                        urlset.append(url_element)

                f.seek(0)
                f.write(str(sitemap_soup.prettify()))
                f.truncate()

if __name__ == '__main__':
    update_files()
