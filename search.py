import json
# from pprint import pprint
import os
from elasticsearch import Elasticsearch
from openai import AzureOpenAI


class Search:
    def __init__(self):
        self.es = Elasticsearch(
            "http://localhost:9200",
            # basic_auth=(username, password),
        )
        # client_info = self.es.info()
        print("Connected to Elasticsearch!")
        # pprint(client_info.body)
        global aoai
        aoai = AzureOpenAI(
            azure_endpoint= "https://allen.openai.azure.com/",
            api_key="954e720ce4b74c948352648233cdc79f",
            api_version="2023-05-15"
        )
        global index_settings
        index_settings = {
            "mappings": {
                "properties": {
                    "id": {"type":"integer"},
                    "title": {"type": "keyword"},
                    "author": {"type": "keyword"},
                    "content": {"type": "text"},
                    "publication_year": {"type": "integer"},
                    "title_vector": {"type": "dense_vector", "dims": 1536},
                    "content_vector": {"type": "dense_vector", "dims": 1536}
                }
            }
        }

    def create_index(self):
        self.es.indices.delete(index="my_documents", ignore_unavailable=True)
        self.es.indices.create(
            index="my_documents",
            body=index_settings
        )

    def get_embedding(self, text):
        response = aoai.embeddings.create(
        input = text,
        model = "embedding"
        )
        return response.data[0].embedding
    

    # def insert_document(self, document):
    #     return self.es.index(
    #         index="my_documents",
    #         document={
    #/             **document,
    #             "embedding": self.get_embedding(document["summary"]),
    #         },
    #     )

    # def insert_documents(self, documents):
    #     operations = []
    #     for document in documents:
    #         operations.append({"index": {"_index": "my_documents"}})
    #         operations.append(
    #             {
    #/                 **document,
    #                 "embedding": self.get_embedding(document["summary"]),
    #             }
    #         )
    #     return self.es.bulk(operations=operations)

    # def reindex(self):
    #     self.create_index()
    #     with open("data.json", "rt") as f:
    #         documents = json.loads(f.read())
    #     return self.insert_documents(documents)

    # def search(self, **query_args):
    #     return self.es.search(index="my_documents", **query_args)

    # def retrieve_document(self, id):
    #     return self.es.get(index="my_documents", id=id)