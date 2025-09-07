
# tests/test_part_service.py

import pytest
import io
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage

from app import db
from app.services import part_service
from app.models.models import Part, RouteTemplate, Stage, User


@pytest.fixture
def mock_csv_file():
    """
    Создает фикстуру с "моковым" CSV-файлом в памяти,
    имитирующим структуру файла "Наборка-№3.csv".
    """
    csv_lines = [
        '"","","","","","",""',
        '"","Наборка №3","","","","",""',
        '"№","Обозначение","Наименование","Кол-во","Размер","Операции","Прим."',
        '"","АСЦБ-000475","Палец","1","","Ток,Фр","Ст3"',
        '"","АСЦБ-000459","Болт осевой","5","S24х530","Св,HRC","30ХГСА"',
        '"","АСЦБ-000461","Ограничитель","4","ф12х140","Ток","Ст45"'
    ]
    csv_content = "\n".join(csv_lines)

    file_storage = FileStorage(
        stream=io.BytesIO(csv_content.encode('utf-8')),
        filename="test_import.csv",
        content_type="text/csv"
    )
    return file_storage


class TestPartService:
    """Тесты для сервиса, отвечающего за бизнес-логику деталей."""

    def test_import_from_hierarchical_csv(self, database, mock_csv_file):
        """
        Тест: Проверяет импорт из CSV-файла со сложной иерархической структурой.
        """
        # 1. Подготовка
        admin_user = User.query.filter_by(username='admin').first()
        mock_config = {'UPLOAD_FOLDER': '/tmp'}

        # 2. Вызываем тестируемую функцию
        added_count, skipped_count = part_service.import_parts_from_excel(
            mock_csv_file, admin_user, mock_config
        )

        # 3. Проверяем результат
        assert added_count == 3
        assert skipped_count == 0

        part1 = db.session.get(Part, "АСЦБ-000475")
        assert part1 is not None
        assert part1.product_designation == "Наборка №3"
        assert part1.name == "Палец"
        
        route1 = RouteTemplate.query.filter_by(name="Ток -> Фр").first()
        assert route1 is not None
        assert part1.route_template_id == route1.id
        
        assert Stage.query.filter_by(name="Ток").first() is not None
        assert Stage.query.filter_by(name="Фр").first() is not None

        # Полные проверки для всех деталей
        part2 = db.session.get(Part, "АСЦБ-000459")
        assert part2 is not None
        assert part2.name == "Болт осевой"
        route2 = RouteTemplate.query.filter_by(name="Св -> HRC").first()
        assert route2 is not None
        assert part2.route_template_id == route2.id
    
    @patch('app.services.part_service.socketio.emit')
    def test_websocket_notification_on_create(self, mock_emit, database):
        """
        Тест: Проверяет, что при создании детали отправляется WebSocket-уведомление.
        """
        admin_user = User.query.filter_by(username='admin').first()
        mock_form = MagicMock()
        mock_form.part_id.data = "NEW-001"
        mock_form.product.data = "Новое Изделие"
        mock_form.name.data = "Новая Деталь"
        mock_form.material.data = "Титан"
        mock_form.size.data = "10x10"
        mock_form.route_template.data = RouteTemplate.query.first().id
        mock_form.quantity_total.data = 10
        mock_form.drawing.data = None

        part_service.create_single_part(mock_form, admin_user, {})
        
        mock_emit.assert_called_once_with('notification', {
            'event': 'part_created',
            'message': f"Пользователь {admin_user.username} создал деталь: NEW-001",
            'part_id': 'NEW-001'
        })

    def test_import_from_malformed_csv_handles_error(self, database):
        """
        Тест "несчастливого пути": Проверяет, что сервис корректно выбрасывает исключение ValueError,
        если в CSV-файле отсутствуют обязательные заголовки.
        """
        # 1. Подготовка: Создаем "сломанный" CSV без нужных заголовков
        csv_content = '"Поле1","Поле2"\n"Значение1","Значение2"'
        malformed_file = FileStorage(
            stream=io.BytesIO(csv_content.encode('utf-8')),
            filename="malformed.csv",
            content_type="text/csv"
        )
        admin_user = User.query.filter_by(username='admin').first()
        mock_config = {'UPLOAD_FOLDER': '/tmp'}

        # 2. Действие и Проверка:
        with pytest.raises(ValueError) as excinfo:
            part_service.import_parts_from_excel(
                malformed_file, admin_user, mock_config
            )
        
        # 3. Дополнительная проверка:
        assert "Не найдены заголовки" in str(excinfo.value)