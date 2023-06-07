from google.cloud import storage

def parse_token(token):
    parsed_token = token.split()
    if len(parsed_token) != 2:
        return None, None
    return parsed_token

def get_bucket_storage(bucket_name):
    storage_client = storage.Client()
    return storage_client.get_bucket(bucket_name)