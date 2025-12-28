#hello.py

"""
因本教程从__init__.py开始,所以不用本文件。
"""
from flask import Flask

app = Flask(__name__)

@app.route('/hy')
def hello():
    return "this is my first flask app. good start!"