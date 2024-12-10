import os
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from pydub import AudioSegment
import uuid

app = Flask(__name__, template_folder='.')

# Configuração de pastas para upload e processamento
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'ogg', 'wav', 'mp3'}

# Garante que a pasta de uploads existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """
    Verifica se o arquivo tem uma extensão permitida
    
    Args:
        filename (str): Nome do arquivo
    
    Returns:
        bool: True se a extensão for permitida, False caso contrário
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def converter_audio_para_wav(arquivo_origem):
    """
    Converte diferentes formatos de áudio para WAV
    
    Args:
        arquivo_origem (str): Caminho do arquivo de áudio original
    
    Returns:
        str: Caminho do arquivo WAV convertido
    """
    # Gera um nome único para o arquivo de saída
    arquivo_wav = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4()}.wav")
    
    # Carrega o arquivo de áudio usando pydub
    audio = AudioSegment.from_file(arquivo_origem, format=arquivo_origem.split('.')[-1])
    
    # Exporta para WAV
    audio.export(arquivo_wav, format="wav")
    
    return arquivo_wav

def transcrever_audio(arquivo_wav):
    """
    Transcreve um arquivo de áudio WAV para texto
    
    Args:
        arquivo_wav (str): Caminho do arquivo WAV
    
    Returns:
        str: Texto transcrito ou mensagem de erro
    """
    recognizer = sr.Recognizer()
    
    try:
        with sr.AudioFile(arquivo_wav) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.record(source)
            
            try:
                # Reconhecimento de fala em português brasileiro
                texto = recognizer.recognize_google(audio, language='pt-BR')
                return texto
            
            except sr.UnknownValueError:
                return "Não foi possível entender o áudio"
            
            except sr.RequestError as e:
                return f"Erro no serviço de reconhecimento: {e}"
    
    except Exception as e:
        return f"Erro ao processar o arquivo: {e}"
    finally:
        # Remove o arquivo WAV temporário
        if os.path.exists(arquivo_wav):
            os.remove(arquivo_wav)

@app.route('/', methods=['GET', 'POST'])
def upload_audio():
    """
    Rota principal para upload e transcrição de áudio
    """
    if request.method == 'POST':
        # Verifica se o arquivo foi enviado
        if 'audio' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['audio']
        
        # Verifica se o nome do arquivo é válido
        if arquivo.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        # Verifica se o arquivo tem extensão permitida
        if arquivo and allowed_file(arquivo.filename):
            # Salva o arquivo temporariamente
            caminho_origem = os.path.join(UPLOAD_FOLDER, arquivo.filename)
            arquivo.save(caminho_origem)
            
            try:
                # Converte para WAV
                arquivo_wav = converter_audio_para_wav(caminho_origem)
                
                # Remove o arquivo original após conversão
                os.remove(caminho_origem)
                
                # Realiza a transcrição
                texto_transcrito = transcrever_audio(arquivo_wav)
                
                return jsonify({'transcricao': texto_transcrito})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
    
    # Renderiza a página de upload para requisições GET
    return render_template('index.html')


if __name__ == '__main__':
    port = os.environ.get('PORT')
    app.debug = True
    app.run(host='0.0.0.0', port=port, debug=True)