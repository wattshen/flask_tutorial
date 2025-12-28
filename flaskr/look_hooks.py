# 1. 导入你的应用实例（flask shell 会自动处理上下文，app 应该已经存在了）
# 如果 app 不存在，手动导入一下（对于你的工厂模式）：
from flaskr import create_app
app = create_app()

# 2. 打印钩子字典
print('-'*60)
print(f'前置钩子after_request_funcs:{app.before_request_funcs}')
print('~'*30)
print(f'后置钩子after_request_funcs:{app.after_request_funcs}')
print('~'*30)
print(f"清理钩子teardown_appcontext_funcs: {app.teardown_appcontext_funcs}")
print('~'*30)
# 3. 退出 Shell
exit()