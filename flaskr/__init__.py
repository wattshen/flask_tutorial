import os

from flask import Flask,request


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    #app.config.from_pyfile('config.py')
    app.config.from_mapping(
        #等价于以下，但from_mapping更友好。app.config是一个方法，不能当字典直接赋值！！！
        #app.config.update({
        #'SECRET_KEY': 'dev',
        #'DATABASE': 'xxx.sqlite'})

        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
        #DATABASE=os.path.join(app.root_path, '..', 'instance', 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        print(f"This page's endpoint(*2) is {request.endpoint * 2 if request.endpoint else "no endpoint"}")  # → 输出: 'hello'
        return f"this is my first flask app. good start!!!! endpoint is {request.endpoint}"

    # register the database commands
    from . import db

    db.init_app(app)

    # set up the debug toolbar
    '''如使用会报错，先禁用！！！
    try:
        from flask_debugtoolbar import DebugToolbarExtension
        app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False # Disable redirect interception for better UX
        app.debug = True
        app.config['DEBUG_TB_PROFILER_ENABLED'] = True
        app.config['DEBUG_TB_HOSTS'] = ['127.0.0.1', '::1', 'localhost']
        toolbar = DebugToolbarExtension(app)
    except ImportError:
        pass
    '''

    # apply the blueprints to the app
    from . import auth
    from . import blog

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    app.add_url_rule("/", endpoint="index")

    return app
