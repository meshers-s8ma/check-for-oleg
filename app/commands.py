
import click
import secrets
import string
import sys
import os
from flask.cli import with_appcontext
from .models.models import db, User, Role, Part, Stage, RouteTemplate, RouteStage, AuditLog, PartNote, ResponsibleHistory, StatusHistory

@click.command('seed')
@with_appcontext
def seed_command():
    """
    Заполняет базу данных начальными данными:
    создает роли и первого администратора.
    """
    if Role.query.count() == 0:
        click.echo("Создание ролей пользователей...")
        Role.insert_roles()
        click.secho("Роли успешно созданы.", fg="green")

    if User.query.count() == 0:
        click.echo("Создание первого администратора ('суперпользователя')...")
        
        if os.environ.get('FLASK_ENV') == 'production':
            alphabet = string.ascii_letters + string.digits
            admin_password = ''.join(secrets.choice(alphabet) for i in range(12))
        else:
            admin_password = 'password123'

        admin_user = User(
            username='admin', 
            role=Role.query.filter_by(name='Administrator').first()
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        db.session.commit()
        
        click.secho("\n✅ Администратор успешно создан.", fg="green")
        click.echo("\n--- Учетные данные администратора ---")
        click.echo(f"   Логин: admin")
        click.echo(f"   Пароль: {admin_password}")
        click.secho("\nВАЖНО: Этот пароль отображается только один раз. Сохраните его в надежном месте.", fg="yellow")
        click.echo("------------------------------------")
    else:
        click.echo("Пользователи уже существуют. Пропуск создания администратора.")

@click.command('seed-cypress')
@with_appcontext
def seed_cypress_command():
    """
    Очищает и заполняет базу данных тестовыми данными,
    необходимыми для прогона E2E-тестов Cypress.
    """
    click.echo("Очистка старых данных...")
    # --- ИЗМЕНЕНИЕ: Правильный порядок удаления для соблюдения внешних ключей ---
    # Сначала удаляем записи из таблиц, которые ССЫЛАЮТСЯ на другие.
    db.session.query(AuditLog).delete()
    db.session.query(PartNote).delete()
    db.session.query(ResponsibleHistory).delete()
    db.session.query(StatusHistory).delete()
    db.session.query(Part).delete() 
    db.session.query(RouteStage).delete()
    db.session.query(User).delete() 
    
    # Теперь можно безопасно удалять "родительские" таблицы.
    db.session.query(Role).delete()
    db.session.query(RouteTemplate).delete()
    db.session.query(Stage).delete()
    
    db.session.commit()
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    click.echo("Создание ролей и пользователей для тестов...")
    Role.insert_roles()
    admin_role = Role.query.filter_by(name='Administrator').first()
    admin = User(username='admin', role=admin_role)
    admin.set_password('password123')
    db.session.add(admin)

    click.echo("Создание тестовых этапов и маршрута...")
    stage1 = Stage(name='Резка')
    stage2 = Stage(name='Сварка')
    route1 = RouteTemplate(name='Стандартный тестовый маршрут', is_default=True)
    db.session.add_all([stage1, stage2, route1])
    db.session.commit() # Коммитим, чтобы получить ID

    rs1 = RouteStage(template_id=route1.id, stage_id=stage1.id, order=0)
    rs2 = RouteStage(template_id=route1.id, stage_id=stage2.id, order=1)
    db.session.add_all([rs1, rs2])

    click.echo("Создание тестовых деталей...")
    part1 = Part(
        part_id='CY-TEST-001',
        product_designation='Тестовое изделие', # То, что ищет тест
        name='Тестовая деталь',
        material='Ст3',
        route_template_id=route1.id
    )
    part2 = Part(
        part_id='OTHER-PART-002',
        product_designation='Другое изделие', # Для теста на поиск
        name='Другая деталь',
        material='Алюминий',
        route_template_id=route1.id
    )
    db.session.add_all([part1, part2])
    db.session.commit()
    click.secho("✅ База данных готова для Cypress-тестов.", fg="green")