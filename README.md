# Virtual Factory Platform

This project is a RAG (Retrieval-Augmented Generation) based Q&A system designed to answer questions related to lithium-ion batteries. It consists of scripts to: 1) scrape Arxiv (https://arxiv.org) for research papers and 2) to generate embeddings for the research papers using OpenAI embeddings. The data and the embeddings are stored in Postgres DB (with the vector extension enabled). It also consists of a Flask application which accepts a question from the user and provides a suitable response using RAG.

**Arxiv Scraper**

The Arxiv scraper is designed to fetch research paper metadata and content from Arxiv based on a specified query. It uses multiprocessing to speed up the scraping process and stores the scraped data in a database. The scraper consists of two main components:

1. **Metadata Scraper**: This component fetches the metadata of research papers, such as titles, authors, and links to the PDF files, based on the search query.
2. **Content Scraper**: This component downloads the PDF files of the research papers and extracts their text content.

The scraper uses a list of user agents to avoid being blocked and includes retry mechanisms to handle transient errors. 

The content of each research paper is split into chunks of 1000 words to improve the quality of embeddings. This chunking process ensures that each chunk is manageable and can be processed efficiently. The chunks are then stored in a PostgreSQL database. Each chunk is associated with its respective research paper and is identified by a chunk number to maintain the order of the content.

**Embedding Generation**

The embedding generation process involves creating vector representations of research papers' content using OpenAI's API. Here is a summary of how it works:

1. **Fetch Papers**: We first fetch research papers from the database which do not yet have an embedding associated with them.
2. **Truncate Content**: The content of each document is truncated to fit within token limits for embedding generation.
3. **Generate Embeddings**: The script generates embeddings for the list of research papers using OpenAI's API.

This ensures that all research papers in the database have corresponding embeddings for efficient retrieval and response generation.

## Features

- **Arxiv Scraper**: Scrapes research paper metadata and content from Arxiv.
- **Embedding Generator**: Generates embeddings for research papers and updates the database.
- **OpenAI Integration**: Uses OpenAI's API to generate embeddings and responses.
- **PostgreSQL Database**: Stores research papers and their embeddings for efficient retrieval.
- **Flask Web Application**: A web interface for users to input their questions and receive answers.


## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/katchke/rag-api.git
    cd rag-api
    ```

2. **Set up a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Run docker compose command with relevant env vars

***Set either one of RUN_SCRAPER or RUN_EMBED_GEN to true to run that pipeline***
```bash
POSTGRES_HOST=pgvector POSTGRES_DB=lithium_ion_content ARXIV_TABLE=arxiv POSTGRES_USER=postgres POSTGRES_PASSWORD=password RUN_SCRAPER=false RUN_EMBED_GEN=false OPENAI_API_KEY=<API_KEY> docker-compose -f docker-compose.yml up
```

## Project Structure

- `main.py`: Implements the Flask web application.
- `generate_embeddings.py`: Generates embeddings for research papers and updates the database.
- `arxiv_scraper.py`: Scrapes research paper metadata and content from Arxiv.
- `utils.py`: Utility functions for database connection and other helper functions.
- `helper.py`: Helper classes and functions for handling research papers.


## Decisions
Certain decisions were made during this assignment to save time because of which the final solution deviates slightly from the assigned problem statement. 

- Research papers were obtained from Arxiv rather than Google Scholar to avoid getting banned by Google for scraping their website
- The search "lithium ion" return approx. 750 papers on Arxiv. All of these were scraped and ingested into DB.
- Avoided too much preprocessing to save time. The application can be further consumed by cleaning the research paper content (for eg: images, equations, citations and so on.)
- The provided directory structure was changed to make codebase simpler for the assignment.
- Testing with a higher number of documents and implementing scaling would have resulted in higher costs (eg: use of AWS, OpenAI credits etc.)


## Scaling strategies
### Data ingestion pipeline
- The data ingestion pipeline consisting of the scraper and the postgres ingestion can be implemented in a tool like AirFlow/Kubeflow to manage scheduling and for further parallelisation of pipeline if needed.
- In general, the entire setup can be deployed on AWS for better scalability. 
    - Rather than maintaining our own database, AWS RDS can be used for improved scaling and maintainability
    - AWS Lambda is also something that can be used for running ingestion and embedding generation scripts using serverless architecture
    - Large-scale scraping of certain sites like Google usually results in bans. This can be avoided by using a proxy or IP rotation strategy which is feasible when deployed on AWS


### Embedding generation 
- The current bottleneck is that OpenAI has a fixed limit in terms of how much tokens can be processed per minute. This limit can be increased with a better plan. 
- Similar parallisation as above could be implemeneted upon increasing the rate limits.


### Q&A application
- In order to handle a large number of conurrent users, the application needs use a production grade web server like Apache rather than the built-in server provided by Flask.
- The application can be deployed on AWS ECS/EKS which allows for scaling of containers/pods based on traffic/CPU utilisation. The ECS/EKS containers/pods would be linked to a load balancer to distribute the traffic. This should enable scaling of the Flask application itself.
- Another bottleneck is the amount of requests that can be sent to OpenAI for chat completion. Merely scaling the flask application is not sufficient due to OpenAI API limits. This limit again depends on the pricing plan being used and can be increased. 