import xlsxwriter
from PyQt6.QtWidgets import QMainWindow, QHeaderView, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QMessageBox, QTableWidget, QTableWidgetItem, \
    QInputDialog, QFileDialog
from PyQt6.QtCore import Qt
import utils

class MainWindow(QMainWindow):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user_id, self.role = user
        self.setGeometry(200, 200, 800, 600)
        utils.center_window(self)
        self.setWindowTitle("Система управления ремонтами")

        layout = QVBoxLayout()

        if self.role == "Клиент":
            self.init_client_ui(layout)
        else:
            self.init_master_ui(layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def init_client_ui(self, layout):
        """Интерфейс для клиента"""
        self.requests_table = QTableWidget(self)
        self.refresh_requests()
        layout.addWidget(self.requests_table)

        buttons_layout = QHBoxLayout()
        create_button = QPushButton("Создать заявку", self)
        create_button.clicked.connect(self.create_request)
        buttons_layout.addWidget(create_button)

        export_button = QPushButton("Экспортировать в Excel", self)
        export_button.clicked.connect(self.export_to_excel)
        buttons_layout.addWidget(export_button)

        search_button = QPushButton("Поиск по заявкам", self)
        search_button.clicked.connect(self.search_requests)
        buttons_layout.addWidget(search_button)

        layout.addLayout(buttons_layout)

    def init_master_ui(self, layout):
        """Интерфейс для мастера"""
        self.requests_table = QTableWidget(self)
        self.refresh_requests()
        layout.addWidget(self.requests_table)
        buttons_layout = QHBoxLayout()

        export_button = QPushButton("Экспортировать в Excel", self)
        export_button.clicked.connect(self.export_to_excel)
        buttons_layout.addWidget(export_button)

        search_button = QPushButton("Поиск по заявкам", self)
        search_button.clicked.connect(self.search_requests)
        buttons_layout.addWidget(search_button)

        update_status_button = QPushButton("Обновить статус заявки", self)
        update_status_button.clicked.connect(self.update_request_status)
        buttons_layout.addWidget(update_status_button)

        layout.addLayout(buttons_layout)

    def refresh_requests(self):
        """Обновление таблицы заявок."""
        cursor = self.db.conn.cursor()
        if self.role == "Мастер":
            cursor.execute("SELECT id, description, status, created_at FROM requests")
        else:
            cursor.execute("SELECT id, description, status, created_at FROM requests WHERE client_id = ?", (self.user_id,))
        
        requests = cursor.fetchall()

        self.requests_table.setRowCount(len(requests))
        self.requests_table.setColumnCount(4)
        self.requests_table.setHorizontalHeaderLabels(["ID", "Описание", "Статус", "Дата создания"])
        self.requests_table.verticalHeader().setVisible(False)
        self.requests_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.requests_table.hideColumn(0)
        self.requests_table.setSortingEnabled(True)
        self.header = self.requests_table.horizontalHeader()
        self.header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.requests_table.setColumnWidth(1, 300)  # Устанавливаем ширину столбца "Описание"

        for row, (req_id, description, status, created_at) in enumerate(requests):
            self.requests_table.setItem(row, 0, QTableWidgetItem(str(req_id)))

            # Ограничиваем текст описания до 50 символов
            short_desc = (description[:50] + "...") if len(description) > 50 else description
            self.requests_table.setItem(row, 1, QTableWidgetItem(short_desc))

            self.requests_table.setItem(row, 2, QTableWidgetItem(status))
            self.requests_table.setItem(row, 3, QTableWidgetItem(created_at))

    def create_request(self):
        """Создание новой заявки"""
        description, ok = QInputDialog.getText(self, "Новая заявка", "Описание проблемы:")
        if not ok or not description:
            return
        self.db.create_request(self.user_id, description)
        QMessageBox.information(self, "Успех", "Заявка создана")
        self.refresh_requests()

    def mark_done(self):
        """Отметить заявку как выполненную"""
        selected = self.requests_table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку для завершения")
            return
        request_id = self.requests_table.item(selected, 0).text()
        self.db.complete_request(request_id)
        QMessageBox.information(self, "Успех", "Заявка выполнена")
        self.refresh_requests()

    def sort_requests(self):
        """Сортировка заявок по статусу."""
        sort_key, ok = QInputDialog.getItem(
            self, "Сортировка заявок", "Выберите поле для сортировки:", ["Статус", "Дата"], editable=False
        )
        if not ok:
            return

        field = "status" if sort_key == "Статус" else "created_at"
        cursor = self.db.conn.cursor()
        cursor.execute(f"SELECT id, description, status, created_at FROM requests ORDER BY {field}")
        sorted_requests = cursor.fetchall()

        self.requests_table.setRowCount(0)  # Очищаем таблицу
        for row, (req_id, description, status, created_at) in enumerate(sorted_requests):
            self.requests_table.insertRow(row)
            self.requests_table.setItem(row, 0, QTableWidgetItem(str(req_id)))
            short_desc = (description[:50] + "...") if len(description) > 50 else description
            self.requests_table.setItem(row, 1, QTableWidgetItem(short_desc))
            self.requests_table.setItem(row, 2, QTableWidgetItem(status))
            self.requests_table.setItem(row, 3, QTableWidgetItem(created_at))

    def export_to_excel(self):
        """Экспорт заявок в Excel."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "Excel Files (*.xlsx)")
        if not file_path:
            return

        cursor = self.db.conn.cursor()
        if self.role == "Клиент":
            cursor.execute("SELECT id, description, status, created_at FROM requests WHERE client_id = ?", (self.user_id,))
        else:
            cursor.execute("SELECT id, description, status, created_at FROM requests")
        requests = cursor.fetchall()

        workbook = xlsxwriter.Workbook(file_path)
        worksheet = workbook.add_worksheet()

        headers = ["ID", "Описание", "Статус", "Дата создания"]
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)

        for row, (req_id, description, status, created_at) in enumerate(requests, start=1):
            worksheet.write(row, 0, req_id)
            worksheet.write(row, 1, description)
            worksheet.write(row, 2, status)
            worksheet.write(row, 3, created_at)

        workbook.close()
        QMessageBox.information(self, "Успех", "Данные успешно экспортированы в Excel.")

    def search_requests(self):
        """Поиск заявок по ключевому слову."""
        keyword, ok = QInputDialog.getText(self, "Поиск заявок", "Введите ключевое слово для поиска:")
        if not ok or not keyword.strip():
            return

        cursor = self.db.conn.cursor()
        query = """
            SELECT id, description, status, created_at
            FROM requests
            WHERE id LIKE ? OR description LIKE ? OR status LIKE ?
        """
        cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
        results = cursor.fetchall()

        self.requests_table.setRowCount(0)
        if results:
            for row, (req_id, description, status, created_at) in enumerate(results):
                self.requests_table.insertRow(row)
                short_desc = (description[:50] + "...") if len(description) > 50 else description
                self.requests_table.setItem(row, 0, QTableWidgetItem(str(req_id)))
                self.requests_table.setItem(row, 1, QTableWidgetItem(short_desc))
                self.requests_table.setItem(row, 2, QTableWidgetItem(status))
                self.requests_table.setItem(row, 3, QTableWidgetItem(created_at))
        else:
            QMessageBox.information(self, "Результаты поиска", "Ничего не найдено.")

    def update_request_status(self):
        """Обновление статуса заявки."""
        selected_row = self.requests_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите заявку для обновления статуса.")
            return

        request_id = self.requests_table.item(selected_row, 0).text()
        statuses = ["Новая", "В процессе", "Завершена"]
        new_status, ok = QInputDialog.getItem(self, "Обновление статуса", "Выберите новый статус:", statuses,
                                              editable=False)
        if not ok:
            return

        with self.db.conn:
            self.db.conn.execute("UPDATE requests SET status = ? WHERE id = ?", (new_status, request_id))
        QMessageBox.information(self, "Успех", "Статус заявки обновлен.")
        self.refresh_requests()
