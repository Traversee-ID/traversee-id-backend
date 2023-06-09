<h1 align="center">
  <br>
    <img src="assets/traversee-logo.png" alt="Traversee" width="200">
  <br>
    Traversee ID
  <br>
    <small style="font-size: 16px"><em>Discover The Unforgettables</em></small>
</h1>

## Table of Contents
- [Table of Contents](#table-of-contents)
- [Architecture](#architecture)
- [Development](#development)
- [Deployment](#deployment)
  - [Firebase](#firebase)
  - [Cloud SQL](#cloud-sql)
  - [Cloud Storage](#cloud-storage)
  - [Secret Manager](#secret-manager)
  - [Service Account](#service-account)
  - [Cloud Scheduler](#cloud-scheduler)
  - [Cloud Run](#cloud-run)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentations)
- [Cloud Computing Team](#cloud-computing-team)

## Architecture
The architecture of this project can be seen in the image below.
![Architecture](assets/architecture.png)

## Development
- Clone this repository
```
git clone https://github.com/Traversee-ID/traversee-id-backend.git
```
- Create `.env` file with the following contents
```
PRIVATE_KEY="<FIREBASE_PRIVATE_KEY>"
PROJECT_ID="<FIREBASE_PROJECT_ID>"
PRIVATE_KEY_ID="<FIREBASE_PRIVATE_KEY_ID>"
CLIENT_EMAIL="<FIREBASE_CLIENT_EMAIL>"
CLIENT_ID="<FIREBASE_CLIENT_ID>"
CLIENT_X509_CERT_URL="<FIREBASE_CLIENT_X509_CERT_URL>"
DATABASE_URI="postgresql://<DB_USER>:<DB_PASSWORD>@<DB_HOST>:<DB_PORT>/<DB_NAME>"
RECOMMENDATIONS_SERVICE="<URL_RECOMMENDATIONS_SERVICE>"
SENTIMENTS_SERVICE="<URL_SENTIMENTS_SERVICE>"
```
- Install project dependencies
```
pip install -r requirements.txt
```
- Run the application
```
flask --app main run -p 8080
```

## Deployment
The unspecified aspects can be adjusted individually or using default values. Additionally, it also allows for enhancing various aspects such as Cloud SQL configuration.

### Firebase
- Enable Firebase Authentication
- Add Android app 
- Generate Firebase Admin private key
- The required outcomes are `PRIVATE_KEY`, `PROJECT_ID`, `PRIVATE_KEY_ID`, `CLIENT_EMAIL`, `CLIENT_ID`, and `CLIENT_X509_CERT_URL`

### Cloud SQL
- Create a PostgreSQL instance
  - PostgreSQL version 13
  - Connections with Public IP, specify CIDR ranges e.g. 0.0.0.0/0
  - Create a new database
  - Create a new user account
- The required outcomes is `DATABASE_URI` with content "postgresql://`DB_USER`:`DB_PASSWORD`@`DB_HOST`:`DB_PORT`/`DB_NAME`"

### Cloud Storage
- Create a bucket
  - Standard default class
  - Enforce public access prevention
  - Fine-grained access control
- The required outcomes is `BUCKET_NAME`

### Secret Manager
- Create several secret for credentials
- An example can be seen in the image below
![Secret Manager](assets/secret-manager.png)

### Service Account
- Create two new service accounts
  - Recommendation Service Invoker
    - Cloud Run Invoker role
  - Traversee Cloud Run Service
    - Secret Manager Secret Accessor role
    - Storage Object Admin role
- An example can be seen in the image below
![Service Account](assets/service-account.png)

### Cloud Scheduler
- Create a new job
  - Frequency: `59 11,23 * * 0-6` (Every day at 11:59 and 23:59)
  - Target type: `HTTP`
  - URL: `<RECOMMENDATIONS_SERVICE>/reload`
  - HTTP method: `POST`
  - Auth header: `Add OIDC token`
  - Service account: `Recommendation Service Invoker`

### Cloud Run
1. Recommendation Service
- The recommendation code service can be accessed [here](https://github.com/Traversee-ID/traversee-id-machine-learning/tree/main/recommendations/service).
- Submit a build using Google Cloud Build
- Create a new service with the recommendation container image
  - Environment variables from secrets: `DATABASE_URI`
  - Ingress control: `All`
  - Authentication: `Allow unauthenticated invocations`
  - Service account: `Traversee Cloud Run Service`
- The required outcomes is `RECOMMENDATIONS_SERVICE` (URL recommendation service)

2. Sentiment Service
- The sentiment code service can be accessed [here](https://github.com/Traversee-ID/traversee-id-machine-learning/tree/main/sentiment_analysis/service).
- Submit a build using Google Cloud Build
- Create a new service with the sentiment container image
  - Ingress control: `All`
  - Authentication: `Allow unauthenticated invocations`
  - Service account: `Traversee Cloud Run Service`
- The required outcomes is `SENTIMENTS_SERVICE` (URL sentiment service)

3. Main Service
- Clone this repository
- Submit a build using Google Cloud Build
- Create a new service with the main container image
  - Environment variables from secrets: `PRIVATE_KEY`, `PROJECT_ID`, `PRIVATE_KEY_ID`, `CLIENT_EMAIL`, `CLIENT_ID`, `CLIENT_X509_CERT_URL`, `DATABASE_URI`, `RECOMMENDATIONS_SERVICE`, and `SENTIMENTS_SERVICE`
  - Ingress control: `All`
  - Authentication: `Allow unauthenticated invocations`
  - Service account: `Traversee Cloud Run Service`

## Project Structure
```
┌───api
│   ├───v1
│   │   ├───models
│   │   │   ├───__init__.py
│   │   │   ├───campaigns.py
│   │   │   ├───forums.py
│   │   │   ├───open_trips.py
│   │   │   └───tourisms.py
│   │   ├───routes
│   │   │   ├───__init__.py
│   │   │   ├───campaigns.py
│   │   │   ├───forums.py
│   │   │   ├───open_trips.py
│   │   │   ├───profiles.py
│   │   │   ├───sentiments.py
│   │   │   └───tourisms.py
│   │   ├───__init__.py
│   │   ├───decorator.py
│   │   ├───extensions.py
│   │   └───helper.py
├───credentials.py
└───main.py
```

## API Documentation
The details of the API documentation can be accessed at [here](https://documenter.getpostman.com/view/2s93sc4spc).

## Cloud Computing Team
| Name | Student ID | Contact |
| - | - | - |
| Muhammad Fikri Haryanto | C181DSX0783 | <a href="https://www.linkedin.com/in/mfikriharyanto"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white" /></a> <a href="https://github.com/mfikriharyanto"><img src="https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white" /></a> |
| Imam Azka Ramadhan Aditia | C181DSX3667 | <a href="https://www.linkedin.com/in/imam-azka-ramadhan"><img src="https://img.shields.io/badge/LinkedIn-0077B5?style=flat&logo=linkedin&logoColor=white" /></a> <a href="https://github.com/imamazka"><img src="https://img.shields.io/badge/GitHub-100000?style=flat&logo=github&logoColor=white" /></a> |
