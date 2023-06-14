import requests
from flask import Blueprint, request
from os import getenv
from ..decorator import authenticated_only

sentiments = Blueprint("sentiments", __name__)

@sentiments.route("/analyze_sentiment", methods=["GET"])
@authenticated_only
def get_sentiment():
    words = request.args.get("words")
    url = getenv("SENTIMENTS_SERVICE")

    response = requests.get(f"{url}/analyze_sentiment?words={words}")
    if response.status_code == 404:
        return {"message": response.json.get("message")}, 404
    
    return {"data": response.json.get("data")}, 200