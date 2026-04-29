from flask import Flask, request, send_file,jsonify,render_template
import os
import time
import subprocess
import threading
import uuid
from werkzeug.utils import secure_filename
from pdf2docx import Converter

app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=50*1024*1024 #50Mb

UPLOAD_FOLDER='uploads'
CONVERTED_FOLDER='converted'

#making sure the folders exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(CONVERTED_FOLDER):
    os.makedirs(CONVERTED_FOLDER)

#making sure the extension is allowed
def allowed_file(filename):
    allowed=['doc','docx','pdf']
    if '.' not in filename:
        return False
    ext=filename.rsplit('.',1)[1].lower() #split one time,  we get only ['extension']
    return ext in allowed #returns TRUE if extension is in allowed

#using threading, i delete files after 5 mins(300 secs)
def delete_later(filepath,delay_seconds=300):
    def delete():
        time.sleep(delay_seconds)
        if os.path.exists(filepath):
            os.remove(filepath)

    t=threading.Thread(target=delete) #thread stops when aplication is terminated
    t.daemon=True
    t.start()        

#converts to docx using pdf2docx
def convert_to_word(input_path,output_path):
    cv=Converter(input_path)#opens file
    cv.convert(output_path)#converts to docx to output
    cv.close()

#converts to pdf using LibreOffice, found this approach online. LibreOffice runs without GUI,thats nice
def convert_to_pdf(input_path,output_dir):
    result=subprocess.run(
        ['soffice','--headless','--convert-to','pdf','--outdir',output_dir,input_path],
                          capture_output=True,
                          text=True,
                          timeout=120
                          ) #headless-no GUi, if takes more then 120s, rasied err
    if result.returncode!=0:
        raise Exception('LibreOffice failed: '+result.stderr)
    
 #converts to docx from doc using LibreOffice as convert-to_pdf
def convert_doc_to_docx(input_path,output_dir):
    result=subprocess.run(
        ['soffice','--headless','--convert-to','docx','--outdir',output_dir,input_path],
                          capture_output=True,
                          text=True,
                          timeout=120
                          ) #headless-no GUi, if takes more then 120s, rasied err
    if result.returncode!=0:
        raise Exception('LibreOffice failed: '+result.stderr)   

#this is python decorator: a function that packs a function
@app.route('/')
def index():
    return render_template('page.html')

#endpoint to get basic info about an uploaded pdf file
@app.route('/info',methods=['POST'])
def get_pdf_info():
    if 'file' not in request.files:
        return jsonify({})
    file = request.files['file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({})
    
    tmp_filename=uuid.uuid4().hex+'.pdf'
    tmp_path=os.path.join(UPLOAD_FOLDER,tmp_filename)
    file.save(tmp_path)
    delete_later(tmp_path,delay_seconds = 60)

    info={}
    try:
        from pypdf import PdfReader #readspdf and exposes Pages and metadata
        reader = PdfReader(tmp_path)
        info['pages']=len(reader.pages) 
        meta=reader.metadata #sometimes aint there the metadata
        if meta:
            if meta.get('/Title'):
                info['Title']=meta['/Title']
            if meta.get('/Author'):
                info['Author']=meta['/Author']
    except Exception as err:
        #returns empy info
        print('Could not read PDF file info: ',err)

    return jsonify(info)    

@app.route('/convert',methods=['POST'])
def convert_file(): # HTTP status code 400-Bad Request
    if 'file' not in request.files:
        return  jsonify({'error':' No file was uploaded'}),400
    file= request.files['file']
    if file.filename=='':
        return jsonify({'error': 'No file selected.'}),400
    if not allowed_file(file.filename):
        return jsonify({'error':'File type not supported'}),400
    
    #saving the file
    input_filename=secure_filename(file.filename) #saves the original file name for download 
    file_ext=input_filename.rsplit('.',1)[1].lower()
    input_path=os.path.join(UPLOAD_FOLDER,input_filename)
    file.save(input_path)
    delete_later(input_path)

    #pdf->docx
    if file_ext=='pdf':
        output_filename=os.path.splitext(input_filename)[0]+'.docx'
        output_path=os.path.join(CONVERTED_FOLDER,output_filename)
        try:
            convert_to_word(input_path,output_path)
        except Exception as err:
            print('Pdf to Word conversion error: ',err)
            return jsonify({'error': 'Conversion failed...'}),500
        
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
    #docx->pdf    
    elif file_ext in ['doc','docx']:  
        #convert from doc->docx
        if file_ext =='doc':
            docx_filename=os.path.splitext(input_filename)[0]+'.docx'
            docx_path=os.path.join(UPLOAD_FOLDER,docx_filename)
            try:
               #calling func in order for libreoffice to convert to pdf
               convert_doc_to_docx(input_path,UPLOAD_FOLDER)

               delete_later(docx_path) #deleting the docx after 5 mins
               input_path=docx_path #new path to new docx document
            except Exception as err:
                return jsonify({'error': 'Could not process.doc file'}),500    
            
            #final path for pdf
        output_filename=os.path.splitext(input_filename)[0]+'.pdf'
        output_path=os.path.join(CONVERTED_FOLDER,output_filename)
        try:
            convert_to_pdf(input_path,CONVERTED_FOLDER) #calling func in order for libreoffice to convert to pdf
        except Exception as err:
            return jsonify({'error': 'Conversion failed...'}),500

        mimetype='application/pdf'    
    else:
        return jsonify({'error':'Unsupported file type'}),400    

    if not os.path.exists(output_path):
        return jsonify({'error':'Conversion failed, output file not found'}),500 #for whatever reason the converted file doesnt exist, return err
            
    delete_later(output_path)
            
    return send_file(
            output_path,
            mimetype=mimetype,
            as_attachment=True,
            download_name=output_filename
            )
            

@app.errorhandler(413) #err 413-payload too large
def file_too_large(err):
    return jsonify({'error':'File is too large, maximum is 50 MB.'}),413

if __name__=='__main__':
    app.run(debug=False,host='127.0.0.1',port=5001) #is just localhost for personal use




        









    