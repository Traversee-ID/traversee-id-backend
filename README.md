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
- [Project Structure](#project-structure)
- [API Documentation](#api-documentations)

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
- Clone this repository
```
git clone https://github.com/Traversee-ID/traversee-id-backend.git
```

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