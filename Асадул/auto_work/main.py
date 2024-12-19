import sys
from PyQt6.QtWidgets import QApplication, QTableWidgetItem
from database import Database
from login_window import LoginWindow




if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    db.create_tables()
    login_window = LoginWindow(db)
    login_window.show()
    sys.exit(app.exec())
