#!/usr/bin/env python
# coding: utf-8

import base64
import datetime
from urllib.parse import urlencode

import requests
#urlendcode can be wrpaped a round a data dictionayry 
# and will turn it inot something that makes sense in a url


## getting the nv variables
import dotenv
import os 
import sys

### loading the env variables
dotenv.load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

print(os.getenv("CLIENT_ID"))

class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True 
    client_id = None
    client_secret = None
    token_url = "https://accounts.spotify.com/api/token"
    
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_client_credentials(self):
        """
        Returns a base 64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_id == None or client_secret == None: 
            raise Exeption("You must set client id and client secret")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
    
    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
                "Authorization": f"Basic {client_creds_b64}" #Basic <base64 encoded client_id:client_secret>
        }
    
    def get_token_data(self):
        return{
            "grant_type": "client_credentials"
        }
    
    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data=token_data, headers=token_headers)
        access_time = datetime.datetime.now()
        valid_request = r.status_code in range(200, 299)
        if not valid_request:
            raise Exeption("Could not authenticate client")
            return False
        data = r.json()
        now = datetime.datetime.now()
        access_token = data["access_token"]
        self.access_token = access_token
        expires_in =  data["expires_in"]
        expires = access_time+datetime.timedelta(seconds=expires_in)
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True
    
    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires <now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token
    
    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        return headers
    
    def get_resource(self, lookup_id, resource_type = 'albums', version = 'v1'):
        endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}" 
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers = headers)
        if r.status_code not in range(200,299):
            return {}
        return r.json()
        
    def get_album(self, _id):
        return self.get_resource(_id, resource_type="albums")
    
    def get_artist(self, _id):
        return self.get_resource(_id, resource_type="artists")
    
    
    ## updating the query string, handling more robust query 
    
    def base_search(self, query_params):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        
        
        lookup_url = f"{endpoint}?{query_params}"
        #r = requests.get(endpoint, data=data, headers=headers)
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    
    def search(self, query = None, operator = None, operator_query= None, search_type='artist'):
        if query==None:
            raise Exeption("Query is required")
        if isinstance(query, dict):
            query= " ".join([f"{k}:{v}" for k,v in query.items()])
        if operator != None and operator_query != None:
            if operator.lower() == "or" or operator.lower() == "not":
                operator = operator.upper()
                if isinstance(operator, str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({
            "q": query,
            "type": search_type
        })
        print(query_params)
        return self.base_search(query_params)
