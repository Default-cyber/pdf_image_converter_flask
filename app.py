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
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Nenhum arquivo selecionado')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('Nenhum arquivo selecionado')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Formato não suportado')
            return redirect(request.url)

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

            # Converte todas as imagens selecionadas (aceita múltiplos uploads)
            image_paths = request.files.getlist('file')
            # Se vier apenas uma imagem
            try:
                if len(image_paths) > 1:
                    imgs = [Image.open(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename))) for f in image_paths]
                else:
                    imgs = [Image.open(in_path)]
            except Exception as e:
                flash('Erro ao ler imagens: ' + str(e))
                return redirect(request.url)

            # Salva no PDF
            try:
                with open(out_pdf_path, "wb") as f:
                    f.write(img2pdf.convert([img.filename for img in imgs]))
            except Exception as e:
                flash('Erro na conversão para PDF: ' + str(e))
                return redirect(request.url)

            return send_file(out_pdf_path, as_attachment=True)

    return render_template('index.html')


if __name__ == '__main__':
    ensure_folders()
    app.run(debug=True)
