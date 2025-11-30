# Diabetes-Chatbot-Agent

## 1. Run requirements installation

```bash 
pip install -r requirements.txt
```

## 2. Set up environment variables
Create a `.env` file in the root directory of the project based on the provided `.env.sample` file. Update the values as needed, especially the `GOOGLE_API_KEY`.

```bash
cp .env.sample .env
```

## 3. Upload knowledge files
```bash
cd backend
python upload_knowledge_files.py
```
Copy the generated file IDs and update the `KNOWLEDGE_FILE_IDS` variable in the `.env` file.

## 4. Run backend server

```bash
cd backend
python run.py
```

## 5. Run frontend application
```bash
cd ../frontend
streamlit run app.py
```
