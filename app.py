from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
from PIL import Image
import PyPDF2
import img2pdf
import os

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.secret_key = 'substitua_por_uma_chave_segura'

# Cria pastas se não existirem
def ensure_folders():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    ensure_folders()  # Garante que as pastas existam antes de usar
    
    if request.method == 'POST':
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

        # Processamento para o primeiro arquivo (PDF -> Imagem)
        file = files[0]
        filename = secure_filename(file.filename)
        in_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(in_path)

        # PDF -> Imagem
        if filename.lower().endswith('.pdf'):
            images = convert_from_path(in_path)
            out_paths = []
            for i, img in enumerate(images, start=1):
                out_name = f"{os.path.splitext(filename)[0]}_page_{i}.png"
                out_path = os.path.join(app.config['OUTPUT_FOLDER'], out_name)
                img.save(out_path, 'PNG')
                out_paths.append(out_name)
            return render_template('index.html', images=out_paths)

        # Imagem -> PDF
        else:
            out_pdf_name = f"{os.path.splitext(filename)[0]}.pdf"
            out_pdf_path = os.path.join(app.config['OUTPUT_FOLDER'], out_pdf_name)

            try:
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
                flash('Erro na conversão para PDF: ' + str(e))
                return redirect(request.url)

    return render_template('index.html')


if __name__ == '__main__':
    ensure_folders()
    app.run(debug=True)