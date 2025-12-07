# Diabetes-Chatbot-Agent

## 1. Run requirements installation

```bash 
pip install -r requirements.txt
```

## 2. Set up environment variables
Create a `.env` file in the root directory of the project based on the provided `.env.sample` file. Update the values as needed.
Do the same for the backend and frontend directories
```bash
cp .env.sample .env
```

## 3. Start caching for knowledge files

```bash 
cd backend
python start_caching.py
```

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

## IMPORTANT NOTE:  
## 6. Stop caching process 
```bash
cd backend
python stop_caching.py
```