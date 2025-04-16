import os
import requests
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, CSVLoader, DirectoryLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import HumanMessage, AIMessage
from langchain.chains import LLMChain

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY not found in .env")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# --- Document processing (PDF/CSV) ---
def process_pdf_from_path(pdf_path):
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore, f"✅ Processed PDF from: {pdf_path}"
    except Exception as e:
        return None, f"❌ Error processing PDF: {e}"

def process_csv_from_path(csv_path):
    try:
        if os.path.isdir(csv_path):
            all_docs = []
            for file in os.listdir(csv_path):
                if file.endswith('.csv'):
                    file_path = os.path.join(csv_path, file)
                    loader = CSVLoader(file_path=file_path)
                    all_docs.extend(loader.load())
            documents = all_docs
        else:
            loader = CSVLoader(file_path=csv_path)
            documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        docs = splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        vectorstore = FAISS.from_documents(docs, embeddings)
        return vectorstore, f"✅ Processed CSV from: {csv_path}"
    except Exception as e:
        return None, f"❌ Error processing CSV: {e}"

# --- Save and load vectorstore ---
def save_vectorstore(vectorstore, path):
    try:
        vectorstore.save_local(path)
        return f"✅ Vectorstore saved at: {path}"
    except Exception as e:
        return f"❌ Error saving vectorstore: {e}"

def load_vectorstore(path):
    try:
        embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
        vectorstore = FAISS.load_local(path, embeddings)
        return vectorstore
    except Exception:
        return None

# --- TMDB API and Tools ---
def call_tmdb_api(endpoint, params=None):
    base_url = "https://api.themoviedb.org/3"
    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "Content-Type": "application/json;charset=utf-8"
    }
    url = f"{base_url}/{endpoint}"
    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        return {"error": str(e)}

def get_popular_movies(_=None):
    if not TMDB_API_KEY:
        return "TMDB API Key not configured."
    res = call_tmdb_api("movie/popular")
    if "error" in res:
        return f"Error fetching popular movies: {res['error']}"
    results = res.get("results", [])
    if not results:
        return "No popular movies found."
    formatted = "Popular movies:\n\n" + "\n".join([f"{i+1}. {m['title']}" for i, m in enumerate(results[:5])])
    return formatted

def search_movies(query):
    if not TMDB_API_KEY:
        return "TMDB API Key not configured."
    if not query:
        return "Please provide a search keyword."
    res = call_tmdb_api("search/movie", {"query": query})
    if "error" in res:
        return f"Error searching movies: {res['error']}"
    results = res.get("results", [])
    if not results:
        return f"No movies found with keyword '{query}'."
    formatted = f"Search results for '{query}':\n\n" + "\n".join([f"{i+1}. {m['title']}" for i, m in enumerate(results[:5])])
    return formatted

def get_movie_recommendations(query):
    if not TMDB_API_KEY:
        return "TMDB API Key not configured."
    if not query:
        return "Please provide a movie name to get recommendations."
    res = call_tmdb_api("search/movie", {"query": query})
    if "error" in res:
        return f"Error searching movie: {res['error']}"
    results = res.get("results", [])
    if not results:
        return f"No movie found with name '{query}'."
    movie_id = results[0]["id"]
    movie_title = results[0]["title"]
    recs = call_tmdb_api(f"movie/{movie_id}/recommendations")
    if "error" in recs:
        return f"Error getting recommendations: {recs['error']}"
    similar = recs.get("results", [])
    if not similar:
        return f"No recommendations found for '{movie_title}'."
    formatted = f"Similar movies for '{movie_title}':\n\n" + "\n".join([f"{i+1}. {m['title']}" for i, m in enumerate(similar[:5])])
    return formatted

def create_agent():
    llm = ChatOpenAI(temperature=0.2, model_name="gpt-4o-mini", api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    tools = [
        Tool(name="PopularMovies", func=get_popular_movies, description="Use when the user wants to see trending or popular movies, hotest film."),
        Tool(name="SearchMovies", func=search_movies, description="Search for movies by name."),
        Tool(name="MovieRecommendations", func=get_movie_recommendations, description="Suggest similar movies.")
    ]
    return initialize_agent(
        tools, llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        verbose=False
    )

# --- Conversation history processing ---
def convert_history_to_langchain(history):
    messages = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role in ["bot", "assistant"]:
            messages.append(AIMessage(content=content))
    return messages

# --- GPT fallback ---
def gpt_fallback(question):
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o-mini", api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    return llm.invoke(question)

# --- Intent classification ---
def classify_intent_with_chain(question):
    greetings = ["chào", "xin chào", "hello", "hi"]
    if any(greet in question.lower() for greet in greetings):
        return "service"
    prompt = PromptTemplate.from_template("""
You are an expert classifier. Classify the user's question into only one of the following types:

- "movie" — for any question about movies, searching for a film, actor, recommendations, or anything about the film industry.
- "service" — for questions related to T3V, support, FAQs, account help, website usage, subscription, or any internal service-related topic.
- "other" — for anything else not related to movies or T3V service.

Some examples:

Q: What is T3V? → service  
Q: How do I reset my password on T3V? → service  
Q: Suggest me a romantic movie. → movie  
Q: Who acted in Inception? → movie  
Q: Tell me about the latest Marvel movie. → movie  
Q: What is the capital of France? → other

Now classify the following:

Question: {question}  
Type:
""")

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run({"question": question}).strip().lower()

# --- Answer from vectorstore (with history) ---
def answer_from_vectorstore(question, chat_history, vectorstore):
    llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini", api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    for msg in convert_history_to_langchain(chat_history):
        memory.chat_memory.add_message(msg)
    prompt = PromptTemplate(template="""
You are a chatbot named T3VMovieBot, friendly and helpful.
Use the information below (embedded from service documentation) to answer user questions.
If no relevant info is found, use the context (chat history) to answer 
or you can use your knowledge to answer the question, just related to film or policies.
Format your answer beautiful

Context: {context}
History: {chat_history}
Question: {question}
Answer:
""", input_variables=["context", "chat_history", "question"])
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": prompt}
    )
    try:
        result = chain.invoke({"question": question})
        return result.get("answer", "No answer available.")
    except Exception as e:
        return f"[🧠] Chain error: {e}\nFallback GPT:\n{gpt_fallback(question)}"


def enrich_movie_info(question, tmdb_response):
    prompt_text = f"""
You are a film critic and expert, known for providing refined, insightful commentary about movies.
Based on the TMDB data provided below, please generate a polished response that highlights the top movies relevant to the query,
and includes additional insights such as trends, noteworthy performances, and critical analysis.
If possible, format your answer in a well-structured list or paragraph.
    
TMDB data:
{tmdb_response}

User query: {question}

Your refined response (e.g., top recommended movies and brief commentary):
"""
    llm = ChatOpenAI(temperature=0.5, model_name="gpt-4o-mini",
                     api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    enriched = llm.invoke(prompt_text)
    return enriched


def answer_from_your_acknowledge(question, chat_history):
    llm = ChatOpenAI(
        temperature=0.2,
        model_name="gpt-4o-mini",
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    for msg in convert_history_to_langchain(chat_history):
        memory.chat_memory.add_message(msg)
    prompt = PromptTemplate(
        template="""
You are a chatbot named T3VMovieBot, friendly and helpful.
Using your knowledge and the chat history below,
please provide the most accurate and helpful answer.

History: {chat_history}
Question: {question}
Answer:
""",
        input_variables=["chat_history", "question"]
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    try:
        chat_history_str = "\n".join([msg.content for msg in memory.chat_memory.messages])
        result = chain.invoke({
            "chat_history": chat_history_str,
            "question": question
        })
        return result.get("text", "").strip()
    except Exception as e:
        return f"[🧠] Chain error: {e}\nFallback GPT:\n{gpt_fallback(question)}"


def process_question(question, chat_history, vectorstore):
    intent = classify_intent_with_chain(question)
    
    if intent == "movie" and TMDB_API_KEY:
        try:
            agent = create_agent()
            tmdb_response = agent.run(question)
            # call enrich info
            enriched = enrich_movie_info(question, tmdb_response)
            return f"[🔍] TMDB data:\n\n{tmdb_response}\n\n[✨] Refined Movie Insights:\n{enriched}"
        except Exception as e:
            return f"[⚠️] TMDB error: {e}\n\n[🧠] GPT fallback:\n{gpt_fallback(question)}"
    
    if intent == "service":
        if vectorstore:
            return answer_from_vectorstore(question, chat_history, vectorstore)
        else:
            return "No service documentation data found. Please upload a document (PDF/CSV) first."
    
    if intent == "other":
        return answer_from_your_acknowledge(question, chat_history)
    
    return f"[🧠] GPT fallback answer (no local data):\n{gpt_fallback(question)}"
