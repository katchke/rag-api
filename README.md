# Rag application api Assignment 

### Question:
You are tasked with developing a scalable RAG-based system that retrieves relevant documents from a large dataset and generates an accurate response using a pre-trained large language model (LLM). 
Note: The system will be used by a high number of concurrent users, so performance, scalability, and resource optimization are crucial.

### Requirements:
- Python
- Pre-trained LLM(e.g GPT or LLama)
- Docker
- PostgresQL


### Deliverables:
- Renowned top 10,000 paper data regarding lithium ion batteries for the rag system using google scholars.
- Implement data preprocessing, indexing, and retrieval,
- Contextual aware response generation using pre-trained model (e.g OpenAI’s GPT, LLamA)
- Scalability and Performance Optimization for several concurrent users - 500 users/sec, and,
- A README.md file with 
    - A brief explanation of how your solution retrieves relevant documents, and generates context aware response, 
        handles scalability for a huge dataset including the pseudocode that implements or outlines the scaling strategies.
    - Link to your Database docker image,
    - Link to your github repository,
    - And any other relevant material to run the application

### Codebase:
The provided sample codebase is built using the flask DDD design pattern, alembic and PostgresQL. Kindly ensure you use the DDD approach to implement the code. Use a docker container to build a PostgresQL Database or any database of your choice image and the application.

Please don’t commit any secret to github, leverage on the .env file.


# Folder structure 
rag-api/
│
├── api-docs/
│
│
│── applications/
│     └── example.py
│
│── docker/
│     ├── app
│     │    └── Dockerfile
│     │
│     └── db
│          ├── Dockerfile
│          └── init.sh
│
│── domains/
│     ├── models.py
│     └── repositories.py
│
│── infrastructures/
│     ├── database/
│     └── config.py
│
│── integration_tests/
│
│
│── migrations/
│   ├── env.py
│   └── script.py.mako
│
│── presentations/
│     └── example.py
│
│
│── scripts/
│
│
├── tests/
│   └── conftest.py
│
│
├── .env
├── .gitignore
├── alembic.ini
├── docker-compose.yml
├── main.py
├── pytest.py
├── README.md
├── requirements.txt
└── routes.py

Install the packages using the requirements.txt file

Run the application `python main.py --port 4001`
