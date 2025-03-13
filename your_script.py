from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
import sqlite3
import bcrypt
from langchain_openai import ChatOpenAI  # Import chatbot-related libraries (replace with actual imports)
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
app = Flask(__name__)
app.secret_key = 'your_secret_key_new'  # Change this to a random secret key
# Chatbot Initialization (Global or Function)
chatbot = None
def init_chatbot():
    global chatbot
    # Chatbot initialization logic:
    # - Load model, documents, etc.
    # - Create ChatOpenAI instance
    loader = TextLoader("data/chatbotdata.txt")  # Replace path as needed
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=0, length_function=len, is_separator_regex=False)
    all_splits = text_splitter.split_documents(docs)
    model_name = "all-mpnet-base-v2"  # Replace path as needed
    encode_kwargs = {'normalize_embeddings': False}
    hf = HuggingFaceEmbeddings(
        model_name=model_name,
        encode_kwargs=encode_kwargs
    )
    vectorstore = Chroma.from_documents(documents=all_splits, embedding=hf)
    chat = ChatOpenAI(openai_api_key="your Open-Ai key")
    template = """You are Tourism support bot. Use the given context to answer students' queries. If the question is completely unrelated to Tourism-related enquiries, please ask the user to only ask Tourism-specific questions.
    {context}
    Question: {question}
    Helpful Answer: """
    QA_CHAIN_PROMPT = PromptTemplate.from_template(template)
    qa_chain = RetrievalQA.from_chain_type(
        llm=chat,
        retriever=vectorstore.as_retriever(),
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}
    )
    chatbot = qa_chain
# Call the initialization function (e.g., before the first route definition)
init_chatbot()


def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
              (id INTEGER PRIMARY KEY AUTOINCREMENT, 
               username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()
def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())  # Hash password before storing
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError as e:
        if 'UNIQUE constraint failed: users.username' in str(e):  # Check for specific error message
            return False  # Indicate username already exists
        else:
            print("Unexpected error adding user:", e)  # Log other errors for debugging
            return False  # Indicate generic error
    finally:
        conn.close()
    return True  # Indicate successful user addition
def get_user(username):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user
def check_password(username, password):
    user = get_user(username)
    if user:
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), user[2]):
                raise Exception('Invalid password')  # Raise custom exception
        except (ValueError, TypeError, IndexError):  # Handle potential bcrypt decoding errors
            raise Exception('Invalid password')  # Raise generic exception
        return user[0]  # Return user id
    raise Exception('User not found')  # Raise exception if user not found
@app.route('/')


def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('main'))
@app.route('/register', methods=['GET', 'POST'])



def register():
    if request.method == 'POST':
        username = request.form['username'].strip()  # Trim leading/trailing whitespaces
        password = request.form['password'].strip()  # Trim leading/trailing whitespaces
        if add_user(username, password):
            return redirect(url_for('login'))
        else:
            error = 'Username already exists'  # Specific error message for username constraint
            return render_template('register.html', error=error)
    return render_template('register.html')
@app.route('/main', methods=['GET', 'POST'])
def main():
    return render_template('main.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        try:
            user_id = check_password(username, password)
            session['username'] = username
            return redirect(url_for('index'))
        except Exception as e:
            error = str(e)
            return render_template('login.html', error=error)
    return render_template('login.html')
@app.route('/styles.css')
def serve_styles():
    return send_from_directory('static', 'styles.css')
@app.route('/scripts.js')
def serve_scripts():
    return send_from_directory('static', 'scripts.js')
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))
@app.post("/answer")
def get_answer():
    if 'username' in session:
        result = chatbot.invoke({'query': request.json['query']})
        return jsonify({"answer": result})
    return jsonify({"error": "User not logged in"})
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
