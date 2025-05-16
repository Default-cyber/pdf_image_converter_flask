from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import traceback
import sys

# Inicialize a aplicação
app = Flask(__name__)
app.secret_key = 'substitua_por_uma_chave_segura'

# Configurações
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'outputs')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB

# Funções auxiliares
def ensure_folders():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    # Verificar se as pastas foram criadas com sucesso
    if not (os.path.exists(UPLOAD_FOLDER) and os.path.exists(OUTPUT_FOLDER)):
        app.logger.error(f"Não foi possível criar as pastas necessárias: {UPLOAD_FOLDER}, {OUTPUT_FOLDER}")
        return False
    return True

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rotas
@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        # Garantir que as pastas existam
        if not ensure_folders():
            flash("Erro ao criar diretórios necessários. Contate o administrador.")
            return render_template('index.html')
        
        if request.method == 'POST':
            # Verificar se há arquivos na requisição
            if 'file' not in request.files:
                flash('Nenhum arquivo selecionado')
                return redirect(request.url)

            files = request.files.getlist('file')
            if not files or files[0].filename == '':
                flash('Nenhum arquivo selecionado')
                return redirect(request.url)

            # Verificar se todos os arquivos têm formatos permitidos
            for file in files:
                if not allowed_file(file.filename):
                    flash(f'Formato não suportado: {file.filename}')
                    return redirect(request.url)

            # Processamento para o primeiro arquivo
            file = files[0]
            filename = secure_filename(file.filename)
            in_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(in_path)

            # PDF -> Imagem
            if filename.lower().endswith('.pdf'):
                try:
                    # Importar aqui para não afetar o carregamento inicial se houver problemas
                    from pdf2image import convert_from_path
                    
                    images = convert_from_path(in_path)
                    out_paths = []
                    for i, img in enumerate(images, start=1):
                        out_name = f"{os.path.splitext(filename)[0]}_page_{i}.png"
                        out_path = os.path.join(app.config['OUTPUT_FOLDER'], out_name)
                        img.save(out_path, 'PNG')
                        out_paths.append(out_name)
                    return render_template('index.html', images=out_paths)
                except Exception as e:
                    app.logger.error(f"Erro na conversão de PDF para imagem: {str(e)}\n{traceback.format_exc()}")
                    flash(f"Erro na conversão de PDF para imagem: {str(e)}")
                    return redirect(request.url)

            # Imagem -> PDF
            else:
                try:
                    # Importar aqui para não afetar o carregamento inicial se houver problemas
                    import img2pdf
                    from PIL import Image
                    
                    out_pdf_name = f"{os.path.splitext(filename)[0]}.pdf"
                    out_pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], out_pdf_name)

                    # Salvar todas as imagens enviadas
                    image_paths = []
                    for file in files:
                        img_filename = secure_filename(file.filename)
                        img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
                        file.save(img_path)
                        image_paths.append(img_path)
                    
                    # Converter as imagens para PDF
                    with open(out_pdf_path, "wb") as f:
                        f.write(img2pdf.convert(image_paths))
                    
                    return send_file(out_pdf_path, as_attachment=True)
                except Exception as e:
                    app.logger.error(f"Erro na conversão para PDF: {str(e)}\n{traceback.format_exc()}")
                    flash(f"Erro na conversão para PDF: {str(e)}")
                    return redirect(request.url)

        return render_template('index.html')
    
    except Exception as e:
        app.logger.error(f"Erro não tratado: {str(e)}\n{traceback.format_exc()}")
        flash(f"Ocorreu um erro inesperado: {str(e)}")
        return render_template('index.html')

# Rota para servir arquivos de saída estáticos
@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename))

if __name__ == '__main__':
    ensure_folders()
    app.run(debug=True)