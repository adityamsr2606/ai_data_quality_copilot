\# AI Data Quality Copilot



An end-to-end data engineering project that uses Databricks, PostgreSQL, FastAPI, and Streamlit to process order data, monitor data quality, and visualize pipeline results.



\## Overview



The AI Data Quality Copilot demonstrates a layered data processing workflow that separates valid records from records requiring further investigation. It provides an interactive dashboard for monitoring data quality and exploring pipeline results.



\## Features



\- \*\*Data ingestion:\*\* Ingest order records into the Bronze layer.

\- \*\*Data transformation:\*\* Process and validate data into Silver and Quarantine layers.

\- \*\*Quality monitoring:\*\* Track validation checks, their statuses, and failed-record counts.

\- \*\*Interactive dashboard:\*\* Explore pipeline metrics, quality results, record previews, and system health.

\- \*\*REST API:\*\* Expose dashboard data through FastAPI endpoints.

\- \*\*PostgreSQL integration:\*\* Store synchronized data quality results.



\## Architecture



```text

Orders CSV

&#x20;   |

&#x20;   v

Databricks Ingestion

&#x20;   |

&#x20;   v

Bronze Layer

&#x20;   |

&#x20;   v

Transformation and Validation

&#x20;   |

&#x20;   +-------------------+

&#x20;   |                   |

&#x20;   v                   v

Silver Layer       Quarantine Layer

&#x20;   |

&#x20;   v

Data Quality Checks

&#x20;   |

&#x20;   v

FastAPI and PostgreSQL

&#x20;   |

&#x20;   v

Streamlit Dashboard

```



\## Technology Stack



\- \*\*Language:\*\* Python

\- \*\*Data engineering:\*\* Databricks, PySpark, Delta tables

\- \*\*Database:\*\* PostgreSQL

\- \*\*Backend:\*\* FastAPI

\- \*\*Dashboard:\*\* Streamlit

\- \*\*Visualization:\*\* Plotly

\- \*\*API documentation:\*\* Swagger UI



\## Sample Results



A verified pipeline run produced the following results:



| Metric | Result |

|---|---:|

| Bronze records | 1,000 |

| Silver records | 952 |

| Quarantined records | 48 |

| Total quality checks | 8 |

| Passed checks | 3 |

| Failed checks | 5 |

| Check pass rate | 37.5% |



\*These are sample results and may vary between executions. The check pass rate measures the proportion of passing checks, not the percentage of valid records.\*



\## Project Structure



```text

ai-data-quality-copilot/

├── backend/

│   ├── main.py

│   ├── database.py

│   └── databricks\_client.py

├── data/

├── database/

├── databricks/

├── frontend/

│   └── app.py

├── .gitignore

├── requirements.txt

└── README.md

```



\## Run Locally



\### 1. Clone the repository



```bash

git clone https://github.com/adityamsr2606/ai\_data\_quality\_copilot.git

cd ai\_data\_quality\_copilot

```



\### 2. Create and activate a virtual environment



```bash

python -m venv .venv

```



Windows PowerShell:



```powershell

.venv\\Scripts\\Activate.ps1

```



\### 3. Install dependencies



```bash

pip install -r requirements.txt

```



\### 4. Configure environment variables



Create a local `.env` file containing the required Databricks and PostgreSQL settings. Never commit credentials, access tokens, or passwords to GitHub.



\### 5. Start the backend



```bash

uvicorn backend.main:app --reload

```



API: `http://127.0.0.1:8000`



API documentation: `http://127.0.0.1:8000/docs`



\### 6. Start the dashboard



Open another terminal and run:



```bash

python -m streamlit run frontend/app.py

```



Dashboard: `http://localhost:8501`



\## Deployment



The dashboard can be deployed through Streamlit Community Cloud. If the frontend depends on FastAPI, the backend must also be deployed to a publicly reachable HTTPS endpoint, with the required environment variables and database access configured securely.



\*\*Live dashboard:\*\* To be added after successful deployment.



\## Security



\- Keep `.env` out of version control.

\- Configure deployment secrets through the hosting platform.

\- Never publish database passwords or API tokens.



\## Project Objective



This project demonstrates practical data engineering skills in data ingestion, layered processing, data validation, quarantine handling, API development, database integration, and data quality visualization.



