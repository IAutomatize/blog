#!/usr/bin/env python3
"""
Script para padronizar todos os artigos HTML:
1. Adicionar seção de artigos relacionados se não existir
2. Padronizar o bloco do Google AdSense no head
"""

import os
import re
from bs4 import BeautifulSoup

def fix_adsense_block(soup):
    """Padroniza o bloco do Google AdSense no head."""
    head = soup.find('head')
    if not head:
        return soup
    
    # Remove todas as variações existentes do AdSense
    adsense_elements = head.find_all(['meta', 'script'], 
        attrs={'name': 'google-adsense-account'})
    adsense_elements.extend(head.find_all('script', 
        src=re.compile(r'pagead2\.googlesyndication\.com')))
    
    for element in adsense_elements:
        element.decompose()
    
    # Adiciona o bloco padrão correto
    adsense_meta = soup.new_tag('meta')
    adsense_meta['name'] = 'google-adsense-account'
    adsense_meta['content'] = 'ca-pub-7469851634184247'
    
    adsense_script = soup.new_tag('script')
    adsense_script['async'] = ''
    adsense_script['src'] = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7469851634184247'
    adsense_script['crossorigin'] = 'anonymous'
    
    # Insere após o último link ou antes do primeiro script
    last_link = head.find_all('link')[-1] if head.find_all('link') else None
    if last_link:
        last_link.insert_after(adsense_meta)
        adsense_meta.insert_after(adsense_script)
    else:
        head.insert(0, adsense_meta)
        adsense_meta.insert_after(adsense_script)
    
    return soup

def add_related_articles_section(soup):
    """Adiciona a seção de artigos relacionados se não existir."""
    # Verifica se já existe a seção
    if soup.find('section', id='related-articles'):
        return soup
    
    # Encontra o main
    main = soup.find('main')
    if not main:
        return soup
    
    # Cria a seção de artigos relacionados
    related_section = soup.new_tag('section', id='related-articles', **{'class': 'section'})
    
    container = soup.new_tag('div', **{'class': 'container'})
    
    title = soup.new_tag('h2', **{'class': 'section-title'})
    title.string = 'Artigos Relacionados'
    
    articles_grid = soup.new_tag('div', **{'class': 'articles-grid'})
    
    # Monta a estrutura
    container.append(title)
    container.append(articles_grid)
    related_section.append(container)
    
    # Adiciona ao final do main
    main.append(related_section)
    
    return soup

def standardize_article(file_path):
    """Padroniza um artigo individual."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
        
        # Aplica as correções
        soup = fix_adsense_block(soup)
        soup = add_related_articles_section(soup)
        
        # Salva o arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        return True
    except Exception as e:
        print(f"❌ Erro ao processar {file_path}: {str(e)}")
        return False

def main():
    """Função principal."""
    print("🚀 Iniciando padronização dos artigos...")
    
    articles_dir = 'articles'
    processed_count = 0
    error_count = 0
    
    # Lista todos os arquivos HTML
    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            
            print(f"📝 Processando: {filename}")
            
            if standardize_article(file_path):
                processed_count += 1
                print(f"  ✅ {filename} - Padronizado com sucesso")
            else:
                error_count += 1
                print(f"  ❌ {filename} - Erro no processamento")
    
    print(f"\n📊 Resumo:")
    print(f"  ✅ Artigos processados com sucesso: {processed_count}")
    print(f"  ❌ Erros: {error_count}")
    print(f"  📁 Total de arquivos: {processed_count + error_count}")
    
    if error_count == 0:
        print("\n🎉 Todos os artigos foram padronizados com sucesso!")
        print("   - Bloco do Google AdSense padronizado")
        print("   - Seção de artigos relacionados adicionada")
    else:
        print(f"\n⚠️  {error_count} artigos tiveram problemas. Verifique os logs acima.")

if __name__ == '__main__':
    main() 