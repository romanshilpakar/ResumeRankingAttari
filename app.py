from flask import Flask, render_template, url_for, request, session, redirect, abort, jsonify
from database import mongo
from werkzeug.utils import secure_filename
import os,re
import spacy, fitz,io
from bson.objectid import ObjectId
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol




def allowedExtension(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ['pdf']

def extract_text_from_pdf(file):
    pdf_document = fitz.open(stream=file.read(), filetype="pdf")
    text = ''
    for page in pdf_document:
        text += page.get_text()
    return text



   

app = Flask(__name__)


app.secret_key = "Resume_screening"


UPLOAD_FOLDER = 'static/uploaded_resumes'
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER

app.config['MONGO_URI']= 'mongodb://localhost:27017/Resumeparser'


mongo.init_app(app)
resumeFetchedData = mongo.db.resumeFetchedData
Applied_EMP=mongo.db.Applied_EMP
IRS_USERS = mongo.db.IRS_USERS
JOBS = mongo.db.JOBS
resume_uploaded = False

###Spacy model
print("Loading Resume Parser model...")
nlp = spacy.load('assets/ResumeModel/output/model-best')
print("Resune Parser model loaded")


@app.route('/')
def index():
    return render_template("index.html")

    
@app.route('/HR', methods=['GET', 'POST'])
def viewdetails():      
    all_results = resumeFetchedData.find({}, {"NAME": 1, "SKILLS": 1, "_id": 0})

    results_list = []
    for result in all_results:
        name = result.get("NAME", "")
        skills = result.get("SKILLS", [])
        results_list.append({"name": name, "skills": skills})
        
    return render_template("CompanyDashboard.html", data=results_list)

    

@app.route('/test')
def test():
    return "Connection Successful"



# @app.route("/uploadResume", methods=['POST'])
# def uploadResume():
#     file = request.files['resume']
#     filename = secure_filename(file.filename)

#     if file and allowedExtension(file.filename):
#         existing_resume = resumeFetchedData.find_one({'ResumeTitle': filename})
#         if existing_resume:
#             resumeFetchedData.delete_one({'ResumeTitle': filename})
#             print("Existing Deleted")

#         ResumeText = extract_text_from_pdf(file)
#         label_list=[]
#         text_list = []
#         dic = {}

#         doc = nlp(ResumeText) 
#         for ent in doc.ents:
#             label_list.append(ent.label_)
#             text_list.append(ent.text) 
#         print("Model work done")
#         for i in range(len(label_list)):
#             if label_list[i] in dic:
#                 # if the key already exists, append the new value to the list of values
#                 dic[label_list[i]].append(text_list[i])
#             else:
#                 # if the key does not exist, create a new key-value pair
#                 dic[label_list[i]] = [text_list[i]]
        
#         # print(dic)
#         dic["ResumeTitle"] = filename
#         result = None  
#         result = resumeFetchedData.insert_one(dic)
#         # resumeFetchedData.insert_one({'filename': filename, 'ResumeText': ResumeText})            
#         if result == None:
#             return render_template("index.html",errorMsg="Problem in Resume Data Storage")  
#         else:
#             return redirect(url_for('viewdetails'))

#     else:
#         return render_template("index.html",errorMsg="Document Type Not Allowed")
    

@app.route("/uploadResume", methods=['POST'])
def uploadResume():
    files = request.files.getlist('resume') 

    for file in files:
        filename = secure_filename(file.filename)

        if file and allowedExtension(file.filename):
            existing_resume = resumeFetchedData.find_one({'ResumeTitle': filename})
            if existing_resume:
                resumeFetchedData.delete_one({'ResumeTitle': filename})
                print("Existing Deleted")

            ResumeText = extract_text_from_pdf(file)
            label_list=[]
            text_list = []
            dic = {}

            doc = nlp(ResumeText) 
            for ent in doc.ents:
                label_list.append(ent.label_)
                text_list.append(ent.text) 
            print("Model work done")
            for i in range(len(label_list)):
                if label_list[i] in dic:
                    # if the key already exists, append the new value to the list of values
                    dic[label_list[i]].append(text_list[i])
                else:
                    # if the key does not exist, create a new key-value pair
                    dic[label_list[i]] = [text_list[i]]
            
            dic["ResumeTitle"] = filename
            result = resumeFetchedData.insert_one(dic)

            if result == None:
                return render_template("index.html", errorMsg="Problem in Resume Data Storage")  

    return redirect(url_for('viewdetails'))


if __name__=="__main__":
    app.run(debug=True)