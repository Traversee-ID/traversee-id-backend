def parse_credentials(credentials):
    credential_list = credentials.split(" ")
    if len(credential_list) != 2:
        return None, None
    return credential_list