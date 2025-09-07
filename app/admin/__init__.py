# Файл: app/admin/__init__.py (ФИНАЛЬНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ)

from flask import Blueprint

# 1. Создаем главный "сборный" блюпринт для всей админки
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# 2. Импортируем дочерние блюпринты ЗДЕСЬ, а не в глобальной области
from .routes import management_routes, part_routes, report_routes, user_routes

# 3. Регистрируем каждый дочерний блюпринт внутри нашего главного.
# Это делает их эндпоинты доступными через префикс 'admin.'
# Например, 'user.login' станет 'admin.user.login'
admin_bp.register_blueprint(management_routes.management_bp)
admin_bp.register_blueprint(part_routes.part_bp, url_prefix='/part')
admin_bp.register_blueprint(report_routes.report_bp, url_prefix='/report')
admin_bp.register_blueprint(user_routes.user_bp, url_prefix='/user')