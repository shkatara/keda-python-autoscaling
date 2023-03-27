from flask import Response, Flask, request
import prometheus_client
from prometheus_client import Counter

## starting the flask app
app = Flask(__name__)

## creating a counter metrics for counting number of requests
c= Counter('python_request_operations_total', 'The total number of processed requests')

## default route to / and each hit to this route will increment the counter with 1 
@app.route("/")
def hello():
    c.inc()
    return "Hello World!"

## exposing metrics on /metrics endpoint. The response has to be through prometheus_client.generate_latest. The generate_latest function generates the latest metrics for that counter.
@app.route("/metrics")
def requests_count():
## with mimetype="text/plain", we are defining to present the information in proper text format. 
## without mimetype, the response is
## # HELP python_request_operations_total The total number of processed requests # TYPE python_request_operations_total counter python_request_operations_total 0.0 # HELP python_request_operations_created The total number of processed requests # TYPE python_request_operations_created gauge python_request_operations_created 1.6799173135400343e+09

## With mimetype, the response is
# HELP python_request_operations_total The total number of processed requests
# TYPE python_request_operations_total counter
#python_request_operations_total 0.0
# HELP python_request_operations_created The total number of processed requests
# TYPE python_request_operations_created gauge
#python_request_operations_created 1.6799173465945044e+09
    return Response(prometheus_client.generate_latest(c),mimetype="text/plain")

## starting the app
if __name__ == "__main__":
    app.run()
