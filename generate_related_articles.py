#!/usr/bin/env python3
"""
Script para gerar artigos relacionados automaticamente
Executa após o update_script.py para adicionar artigos relacionados a todos os artigos
"""

import os
import re
from datetime import datetime
from bs4 import BeautifulSoup
from collections import Counter

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

def get_article_metadata(file_path):
    """Extrai metadados de um arquivo HTML de artigo."""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    # Extração básica de metadados
    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else ''

    # Keywords/tags
    meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
    tags = []
    if meta_keywords and meta_keywords.get('content'):
        tags = [tag.strip() for tag in meta_keywords['content'].split(',')]
    
    # Categoria
    category = 'Tecnologia'
    meta_category = soup.find('meta', attrs={'name': 'category'})
    if meta_category and meta_category.get('content'):
        category = meta_category['content'].strip()
    else:
        # Tenta extrair da meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content') and 'Em ' in meta_desc['content']:
            category = meta_desc['content'].split('Em ')[1].split('.')[0]
    
    # Autor
    meta_author = soup.find('meta', attrs={'name': 'author'})
    author = 'IAUTOMATIZE'
    if meta_author and meta_author.get('content'):
        author = meta_author['content'].strip()
    
    # Descrição
    meta_description = soup.find('meta', attrs={'name': 'description'})
    excerpt = ''
    if meta_description and meta_description.get('content'):
        excerpt = meta_description['content'].strip()
    
    # Imagem
    meta_image = soup.find('meta', attrs={'property': 'og:image'})
    image_url = '../assets/images/articles/default.jpg'
    if meta_image and meta_image.get('content'):
        image_url = meta_image['content'].strip()
    
    # Data
    publish_date = datetime.fromtimestamp(os.path.getmtime(file_path))
    
    # Palavras-chave do conteúdo
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

def formatar_data_pt(dt):
    """Formata data para português."""
    meses = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
             "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
    return f"{dt.day:02d} de {meses[dt.month]} de {dt.year}"

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
            no_related_msg['style'] = "text-align: center; color: #666; font-style: italic;"
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
            
        print(f"✅ Artigos relacionados adicionados em {os.path.basename(file_path)}")
        
    except Exception as e:
        print(f"❌ Erro ao adicionar artigos relacionados em {file_path}: {str(e)}")

def main():
    """Função principal."""
    print("🚀 Iniciando geração de artigos relacionados...")
    
    articles_dir = 'articles'
    all_articles_data = {}
    
    # Coleta metadados de todos os artigos
    print("\n📖 Coletando metadados dos artigos...")
    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            try:
                metadata = get_article_metadata(file_path)
                article_id = filename.replace('.html', '')
                all_articles_data[article_id] = metadata
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ❌ Erro ao processar {filename}: {str(e)}")
    
    print(f"\n📊 Total de artigos processados: {len(all_articles_data)}")
    
    # Adicionar artigos relacionados a cada artigo
    print("\n🔗 Adicionando artigos relacionados...")
    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            add_related_articles_to_article(file_path, all_articles_data, all_articles_data)
    
    print("\n✅ Processo concluído! Artigos relacionados foram adicionados a todos os artigos.")

if __name__ == '__main__':
    main() 