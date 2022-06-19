from flask import Flask
from flask import request
import json

from hotel_search import HotelSearchUtils

class FlaskApp(Flask):

    def __init__(self, *args, **kwargs):
        super(FlaskApp, self).__init__(*args, **kwargs)
        self.hotel_search_utils = HotelSearchUtils()


app = FlaskApp(__name__)

@app.route("/")
def helloWorld():
    str_text = 'hello world\nserver is up :)'
    return str_text

@app.route("/get_result")
def result():
    query_text = request.args.get('q', type=str)
    report_id = request.args.get('report_id', type=str)
    top_n = request.args.get('top_n', default=1, type=int)
    result_dict = {}
    result_dict['result'] = app.hotel_search_utils.get_top_hotels(query_text, report_id, top_n)
    return json.dumps(result_dict)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)
