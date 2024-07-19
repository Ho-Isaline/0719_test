import re
from flask import Flask, render_template, request
from search import Search

app = Flask(__name__)
app.config['DEBUG'] = True
es = Search()

@app.get('/')
def index():
    return render_template('index.html')



@app.post('/')
def handle_search():
    query = request.form.get('query', '')
    filters, parsed_query = extract_filters(query)
    from_ = request.form.get("from_", type=int, default=0)
    
    if parsed_query:
        search_query = {
            "must": {
                "multi_match": {
                    "query": parsed_query,
                    "fields": ["name", "summary", "content"],
                }
            }
        }
    else:
        search_query = {"must": {"match_all": {}}}
        
    print(parsed_query, search_query)
    # exit()
    results = es.search(
        query={"bool": {**search_query, **filters}},
        knn={
            "field": "embedding",
            "query_vector": es.get_embedding(parsed_query),
            "k": 10,
            "num_candidates": 50,
            **filters,
        },
        rank={"rrf": {}},
        aggs={
            "category-agg": {
                "terms": {
                    "field": "category.keyword",
                }
            },
            "year-agg": {
                "date_histogram": {
                    "field": "updated_at",
                    "calendar_interval": "year",
                    "format": "yyyy",
                },
            },
        },
        size=5,
        from_=from_,
    )
    aggs = {
        "Category": {
            bucket["key"]: bucket["doc_count"]
            for bucket in results["aggregations"]["category-agg"]["buckets"]
        },
        "Year": {
            bucket["key_as_string"]: bucket["doc_count"]
            for bucket in results["aggregations"]["year-agg"]["buckets"]
            if bucket["doc_count"] > 0
        },
    }
    results["hits"]["hits"]
    print(results)
    # query_vector = generate_embedding(query)
    # search_body = {
    #     "size": top_k,
    #     "query": {
    #         "script_score": {
    #             "query": {"match_all": {}},
    #             "script": {
    #                 "source": """
    #                 double titleScore = cosineSimilarity(params.query_vector, 'title_vector') * 2;
    #                 double contentScore = cosineSimilarity(params.query_vector, 'content_vector');
    #                 return titleScore + contentScore + 1.0
    #                 """,
    #                 "params": {"query_vector": query_vector}
    #             }
    #         }
    #     }
    # }
    # response = es.search(index=index_name, body=search_body)
    return render_template(
        "index.html",
        results=results["hits"]["hits"],
        query=query,
        from_=from_,
        total=results["hits"]["total"]["value"],
        aggs=aggs,
    )

@app.get('/document/<id>')
def get_document(id):
    document = es.retrieve_document(id)
    title = document["_source"]["name"]
    paragraphs = document["_source"]["content"].split("\n")
    return render_template("document.html", title=title, paragraphs=paragraphs)

@app.cli.command()
def reindex():
    """Regenerate the Elasticsearch index."""
    response = es.reindex()
    # # print(
    #     f'Index with {len(response["items"])} documents created '
    #     f'in {response["took"]} milliseconds.'
    # # )
    
def extract_filters(query):
    filters = []

    filter_regex = r'category:([^\s]+)\s*'
    m = re.search(filter_regex, query)
    if m:
        filters.append({
            'term': {
                'category.keyword': {
                    'value': m.group(1)
                }
            }
        })
        query = re.sub(filter_regex, '', query).strip()

    return {'filter': filters}, query

