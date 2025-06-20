import re
import math
from collections import Counter
from textblob import TextBlob
from bs4 import BeautifulSoup

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

def calculate_readability(text):
    """Calcula o índice de leiturabilidade Flesch."""
    if not text:
        return {"score": 0, "grade": "N/A"}
    
    # Contagem básica
    words = re.findall(r'\b\w+\b', text.lower())
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]
    
    if not words or not sentences:
        return {"score": 0, "grade": "N/A"}
    
    # Cálculo do índice Flesch adaptado para português
    word_count = len(words)
    sentence_count = len(sentences)
    syllable_count = sum(count_syllables_pt(word) for word in words)
    
    # Fórmula adaptada para português
    score = 206.835 - (1.015 * (word_count / sentence_count)) - (84.6 * (syllable_count / word_count))
    
    # Classificação
    if score >= 90:
        grade = "Muito fácil"
    elif score >= 80:
        grade = "Fácil"
    elif score >= 70:
        grade = "Razoavelmente fácil"
    elif score >= 60:
        grade = "Padrão"
    elif score >= 50:
        grade = "Razoavelmente difícil"
    elif score >= 30:
        grade = "Difícil"
    else:
        grade = "Muito difícil"
    
    return {"score": round(score, 1), "grade": grade}

def count_syllables_pt(word):
    """Estimativa de sílabas para português."""
    word = word.lower()
    # Conta vogais
    vowels = "aeiouyáàâãéèêíìîóòôõúùûç"
    count = 0
    prev_is_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_is_vowel:
            count += 1
        prev_is_vowel = is_vowel
    
    # Ajustes para ditongos, etc.
    for pattern in ["ai", "ao", "ei", "eu", "ia", "ie", "io", "iu", "oi", "ou", "ua", "ue", "ui", "uo"]:
        count -= word.count(pattern)
    
    # Garantir pelo menos 1 sílaba
    return max(1, count)

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

# Exemplo de uso:
if __name__ == "__main__":
    # Integrando com update_script.py
    import os
    
    articles_dir = 'articles'
    all_articles_data = {}
    
    for filename in os.listdir(articles_dir):
        if filename.endswith('.html'):
            file_path = os.path.join(articles_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            text = extract_text_from_html(html_content)
            readability = calculate_readability(text)
            keywords = extract_keywords(text)
            
            article_id = filename.replace('.html', '')
            all_articles_data[article_id] = {
                'readability': readability,
                'keywords': keywords,
                # Outros metadados seriam adicionados aqui
            }
    
    # Gerar relatório de leiturabilidade
    with open('readability_report.md', 'w', encoding='utf-8') as f:
        f.write("# Relatório de Leiturabilidade\n\n")
        for article_id, data in all_articles_data.items():
            f.write(f"## {article_id}\n")
            f.write(f"- Índice Flesch: {data['readability']['score']}\n")
            f.write(f"- Classificação: {data['readability']['grade']}\n")
            f.write(f"- Palavras-chave: {', '.join(data['keywords'])}\n\n")
