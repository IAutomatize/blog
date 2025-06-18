import os
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def get_article_metadata(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''

    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    tags = [tag.strip() for tag in meta_keywords['content'].split(',')] if meta_keywords else []
    
    # Assuming the category is in a meta tag, otherwise, we need to adapt this
    meta_category = soup.find('meta', attrs={'name': 'category'})
    category = meta_category['content'].strip() if meta_category else ''

    return {
        'title': title,
        'tags': tags,
        'category': category,
        'path': file_path
    }

def update_files():
    articles_dir = 'articles'
    recent_articles = []
    three_days_ago = datetime.now() - timedelta(days=3)

    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime > three_days_ago:
                recent_articles.append(get_article_metadata(file_path))

    # Update index.html
    with open('index.html', 'r+', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

        # This is a placeholder for where you want to update the breadcrumbs/tags
        # You will need to adapt this to your index.html structure
        # For example, find a div by id and replace its content
        tags_container = soup.find(id='tags-container')
        if tags_container:
            # Clear existing tags and add new ones
            tags_container.clear()
            all_tags = set()
            for article in recent_articles:
                for tag in article['tags']:
                    all_tags.add(tag)
            
            for tag in all_tags:
                tag_element = soup.new_tag('a', href=f'/tags/{tag}.html')
                tag_element.string = tag
                tags_container.append(tag_element)

        f.seek(0)
        f.write(str(soup))
        f.truncate()

    # Update sitemap.xml
    with open('sitemap.xml', 'r+', encoding='utf-8') as f:
        sitemap_soup = BeautifulSoup(f, 'xml')
        
        existing_urls = [loc.text for loc in sitemap_soup.find_all('loc')]

        for article in recent_articles:
            url = f"https://iautomatize.github.io/blog/{article['path'].replace(os.path.sep, '/')}"
            if url not in existing_urls:
                url_element = sitemap_soup.new_tag('url')
                loc_element = sitemap_soup.new_tag('loc')
                loc_element.string = url
                url_element.append(loc_element)
                sitemap_soup.find('urlset').append(url_element)

        f.seek(0)
        f.write(str(sitemap_soup))
        f.truncate()


if __name__ == '__main__':
    update_files()
