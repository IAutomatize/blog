import os

# 1. DEFINA O CÓDIGO DO ADSENSE QUE VOCÊ QUER INSERIR
# Coloquei um comentário para ficar organizado no seu HTML
adsense_code_block = """
    <meta name="google-adsense-account" content="ca-pub-7469851634184247">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7469851634184247"
     crossorigin="anonymous"></script>
"""

# 2. DEFINA A PASTA ONDE ESTÃO SEUS ARTIGOS
articles_directory = 'articles'

# 3. DEFINA UMA LINHA DE "ÂNCORA" NO SEU HTML
# O script vai inserir o código do AdSense ANTES dessa linha.
# Pelo seu template, a linha do favicon é um ótimo lugar.
anchor_line = '<link rel="icon" type="image/x-icon" href="/favicon.ico">'

# --- O SCRIPT COMEÇA AQUI ---
print("Iniciando a adição do código AdSense aos artigos...")
files_processed = 0
files_updated = 0

# Percorre todos os arquivos na pasta de artigos
for filename in os.listdir(articles_directory):
    if filename.endswith('.html'):
        files_processed += 1
        file_path = os.path.join(articles_directory, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Verifica se o código já existe para não adicionar de novo
            if 'ca-pub-7469851634184247' in content:
                print(f"-> Ignorando '{filename}': Código já existe.")
                continue

            # Verifica se a linha âncora existe no conteúdo
            if anchor_line in content:
                # Substitui a âncora pela combinação do código AdSense + âncora
                new_content = content.replace(anchor_line, f"{adsense_code_block}\n    {anchor_line}")

                # Salva o arquivo com o novo conteúdo
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                
                print(f"✅ Atualizado com sucesso: '{filename}'")
                files_updated += 1
            else:
                print(f"⚠️ Atenção '{filename}': Linha âncora não encontrada. Arquivo não modificado.")

        except Exception as e:
            print(f"❌ Erro ao processar '{filename}': {e}")

print("\n--- Processo Concluído ---")
print(f"Total de arquivos HTML encontrados: {files_processed}")
print(f"Total de arquivos atualizados: {files_updated}")