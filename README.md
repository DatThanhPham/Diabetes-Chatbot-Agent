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

## 3. Run backend server

```bash
cd backend
python run.py
```

## 4. Run frontend application
```bash
cd ../frontend
streamlit run app.py
```
