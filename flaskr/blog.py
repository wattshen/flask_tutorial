from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from .auth import login_required
from .db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    '''
    db.execute()执行后得到一个游标对象，通过以下取出：
    fetchone():每次返回结果中的最前一行，例(1,'title1') fetchone()[0]的值为1
    fetchall()：一次返回全部结果的列表，例[(1,'title1'),(2,'title2'),(3,'title3')] fetchall()[0]的值为(1,'title1')
    '''
    db = get_db()
      
    '''
    这是第一版的分页
    
    page = request.args.get('page', 1, type=int)
    per_page = 5
    offset = (page - 1) * per_page#巧妙算法

    total = db.execute("select count(*) from post").fetchone()[0]
    total_pages = (total + per_page - 1)// per_page#巧妙算法

    posts = db.execute(
        "SELECT p.id, title, body, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id "
        " ORDER BY created DESC limit ? offset ?",(per_page,offset)
        ).fetchall()
    return render_template("blog/index.html", posts=posts, page=page, total_pages=total_pages)
    '''

    '''
    糅合搜索、标签后的分页
    '''
    page = request.args.get('page', 1, type=int)
    if page < 1:
        page = 1
    if page > 100:
        page = 100
    per_page = request.args.get('per_page',5, type=int)
    if per_page < 1:
        per_page = 1
    if per_page > 100:
        per_page = 100
    tag_name = request.args.get('tag')
    search_query = request.args.get('q')
    offset = (page - 1) * per_page#巧妙算法
    
    query_base = '''
        SELECT p.id, p.title, p.body, p.created, p.author_id, u.username,
         GROUP_CONCAT(t.name) as tags
         FROM post p
         JOIN user u ON p.author_id = u.id
         LEFT JOIN post_tag pt ON p.id = pt.post_id
         LEFT JOIN tag t ON pt.tag_id = t.id
    '''
    query_count = "SELECT count(DISTINCT p.id) FROM post p"
    params = []
    where_clauses = []
    
    # 标签过滤
    if tag_name:
        '''
        query_base += " JOIN post_tag pt ON p.id = pt.post_id JOIN tag t ON pt.tag_id = t.id"
        query_count += " JOIN post_tag pt ON p.id = pt.post_id JOIN tag t ON pt.tag_id = t.id"
        where_clauses.append("t.name = ?")
        '''
        # 使用子查询过滤
        where_clauses.append("p.id IN (SELECT pt.post_id FROM post_tag pt JOIN tag t ON pt.tag_id = t.id WHERE t.name = ?)")
        params.append(tag_name)
    
    # 标题搜索
    if search_query:
        where_clauses.append("p.title like ?")
        params.append(f"%{search_query}%")
    
    # 拼接 WHERE子句
    if where_clauses:
        clauses_str = " WHERE " + " AND ".join(where_clauses)
        query_base += clauses_str
        query_count += clauses_str

    # 获取总数
    total = db.execute(query_count, params).fetchone()[0]
    total_pages = (total + per_page -1) // per_page

    # 添加排序和分页
    #query_base += " ORDER BY p.created DESC LIMIT ? OFFSET ?"
    #必须加 GROUP BY p.id 否则 GROUP_CONCAT 会把所有帖子的标签拼成一行
    query_base += "GROUP BY p.id ORDER BY p.created DESC LIMIT ? OFFSET ?" 
    params.extend([per_page, offset])
    posts = db.execute(query_base, params).fetchall()
    return render_template("blog/index.html", posts=posts, page=page, total_pages=total_pages, current_tag=tag_name, search_query=search_query)




def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, title, body, created, author_id, username, GROUP_CONCAT(t.name) as tags"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " LEFT JOIN post_tag pt ON p.id = pt.post_id"
            " LEFT JOIN tag t ON pt.tag_id = t.id"
            " WHERE p.id = ?"
            " GROUP BY p.id",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post



@bp.route("/<int:id>")
def detail(id):
    """show a post detail."""
    post = get_post(id, check_author=False)
    #return render_template(url_for("detail.html"),post=post)
    '''
    render_template : 
         1)需要的是硬盘上的一个模板文件。
         2)post=post 是将view控制器中的post(右)传给html模板(左post)
         3)如果有更多参数可以**关键字解包:
            post = get_post(id)
            comments = get_comments(id)
            # 或者 return render_template("blog/detail.html", **locals())
            context = {'post': post, 'comments': comments}
            return render_template("blog/detail.html", **context)
    url_for()是按端点(函数名)等来生成url,返回的是一个ur,不是模板文件
    所以不能用url_for

    '''
    db = get_db()

    comments = db.execute(
        "SELECT c.body, c.created, u.username"
        " FROM comment c JOIN user u ON c.user_id = u.id"
        " WHERE c.post_id = ? "
        " ORDER BY c.created DESC ",
        (id,)
    ).fetchall()

    like_count = db.execute(
        "SELECT COUNT(*) FROM user_like WHERE post_id = ?",
        (id,)
    ).fetchone()[0]

    liked = False
    if g.user:
        liked = db.execute(
            "SELECT 1 FROM user_like WHERE user_id = ? and post_id = ?",
            (g.user['id'], id)
        ).fetchone() is not None
    
    return render_template("blog/detail.html", post=post, comments=comments, like_count=like_count, liked=liked)

@bp.route("/<int:id>/like", methods=("POST",))
@login_required
def like(id):
    db = get_db()
    db.execute(
        "INSERT OR IGNORE INTO user_like (user_id, post_id) VALUES (?, ?)",
        (g.user['id'], id)
    )
    db.commit()
    return redirect(url_for("blog.detail", id=id))

@bp.route("/<int:id>/unlike", methods=("POST",))
@login_required
def unlike(id):
    db = get_db()
    db.execute(
        "DELETE FROM user_like WHERE user_id = ? AND post_id = ?",
         (g.user['id'], id)
    )
    db.commit()
    return redirect(url_for('blog.detail', id=id))

@bp.route("/<int:id>/comment", methods = ("POST",))
@login_required
def comment(id):
    body = request.form["body"]
    error = None

    if not body:
        error = '评论内容不可为空'
    
    if error:
        flash(error)
    else:
        db = get_db()
        db.execute(
            "INSERT INTO comment (body, user_id, post_id) VALUES (?, ?, ?)",
            (body, g.user['id'], id)
        )
        db.commit()
    
    return redirect(url_for("blog.detail",id=id))

def save_tags(db, post_id, tags_str):#接收db参数方便在调用处关闭连接且节约、连贯。是工具函数区别于路由函数（视图函数）
    if not tags_str:
        return
    # 分割标签并去重
    tag_names = set(t.strip() for t in tags_str.split(",") if t.strip())
    for tag_name in tag_names:
        # 查找或创建标签，返回ID
        tag = db.execute('SELECT id FROM tag WHERE name = ?',(tag_name,)).fetchone()
        if not tag:
            cursor  = db.execute("INSERT INTO tag (name) VALUES (?)", (tag_name,))
            tag_id = cursor.lastrowid
        else:
            tag_id = tag['id']
        # 关联文章和标签
        db.execute("INSERT OR IGNORE INTO post_tag (post_id, tag_id) VALUES (?, ?)", (post_id, tag_id))


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        tags = request.form.get("tags") #获取标签输入
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            cursor = db.execute(
                "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
                (title, body, g.user["id"]),
            )
            post_id = cursor.lastrowid#由游标方法获取id
            save_tags(db, post_id, tags)
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        title = request.form["title"]
        body = request.form["body"]
        tags = request.form.get("tags")
        error = None

        if not title:
            error = "Title is required."

        if error is not None:
            flash(error)#在页面展示错误消息
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
            )
            db.execute("DELETE FROM post_tag WHERE post_id = ?", (id,))
            save_tags(db, id, tags)
            db.commit()
            return redirect(url_for("blog.index"))
        '''
        db = get_db()
        current_tags = db.execute(
            "SELECT t.name FROM tag t JOIN post_tag pt ON t.id = pt.tag_id WHERE pt.post_id = ?", (id,)
        ).fetchall()
        tags_str = ", ".join([row['name'] for row in current_tags]) 
        return render_template("blog/update.html", post=post, tags = tags_str)
        '''
    return render_template("blog/update.html", post=post, tags=post['tags'])


@bp.route("/<int:id>/delete", methods=("get",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)#**“副作用调用” (Call for Side Effects)
    db = get_db()
    '''
    在这里，我们调用 get_post(id) 不是为了要它的返回值（那个帖子对象），而是为了利用它的“副作用”——也就是它的检查机制。
    1)get_post(id) 会检查post是否存在,如果不存在会抛出404错误
    2)如果存在,会检查当前用户是否是作者,如果不是会抛出403错误
    一行相当于以下多行：

    post = get_post(id)
    if g.user['id'] == post['author_id']:
        db.execute("DELETE FROM post WHERE id = ?", (id,))
        db.commit()
        return redirect(url_for("blog.index"))
    else:
        abort(403)

    '''

    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))


