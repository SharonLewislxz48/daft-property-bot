#!/usr/bin/env python3
"""
Простая версия для тестирования парсинга сообщений Telegram
"""

import re
import tkinter as tk
from tkinter import messagebox, scrolledtext
from dataclasses import dataclass
from typing import Optional

@dataclass
class PropertyListing:
    """Данные об объявлении недвижимости"""
    title: str
    address: str
    price: str
    bedrooms: str
    url: str
    user: str

class TelegramParser:
    """Парсер сообщений Telegram"""
    
    def __init__(self):
        self.property_pattern = re.compile(
            r'🏠\s+(.+?)\n\n📍\s+Адрес:\s+(.+?)\n💰\s+Цена:\s+(.+?)\n🛏️\s+Спальни:\s+(.+?)\n\n🔗\s+.*?\((https://www\.daft\.ie/[^)]+)\)\s*\n\n👤\s+От пользователя:\s+(.+)',
            re.MULTILINE | re.DOTALL
        )
    
    def parse_property_message(self, text: str) -> Optional[PropertyListing]:
        """Парсинг сообщения с объявлением"""
        match = self.property_pattern.search(text)
        if match:
            return PropertyListing(
                title=match.group(1).strip(),
                address=match.group(2).strip(),
                price=match.group(3).strip(),
                bedrooms=match.group(4).strip(),
                url=match.group(5).strip(),
                user=match.group(6).strip()
            )
        return None

class TestApp:
    """Тестовое приложение для проверки парсинга"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Тест парсера Telegram сообщений")
        self.root.geometry("800x600")
        
        self.parser = TelegramParser()
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Заголовок
        title_label = tk.Label(self.root, text="Тест парсера сообщений Daft.ie", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Инструкция
        instruction = tk.Label(self.root, 
                              text="Вставьте сообщение из Telegram в поле ниже и нажмите 'Парсить'",
                              font=('Arial', 10))
        instruction.pack(pady=5)
        
        # Поле для ввода текста
        tk.Label(self.root, text="Исходное сообщение:", font=('Arial', 12, 'bold')).pack(anchor='w', padx=10)
        self.text_input = scrolledtext.ScrolledText(self.root, height=10, width=90)
        self.text_input.pack(padx=10, pady=5, fill='both', expand=True)
        
        # Пример сообщения
        example_text = """🏠 4 Grosvenor Lodge, Dublin 6, Rathmines, Dublin 6

📍 Адрес: Rathmines,  Dublin 6
💰 Цена: €2,182
🛏️ Спальни: 4 спален

🔗 Посмотреть объявление (https://www.daft.ie/for-rent/house-4-grosvenor-lodge-dublin-6-rathmines-dublin-6/6166624)


👤 От пользователя: @Barss20"""
        
        self.text_input.insert('1.0', example_text)
        
        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        parse_button = tk.Button(button_frame, text="🔍 Парсить сообщение", 
                               command=self.parse_message, bg='#4CAF50', fg='white',
                               font=('Arial', 12, 'bold'), padx=20, pady=5)
        parse_button.pack(side='left', padx=5)
        
        clear_button = tk.Button(button_frame, text="🗑️ Очистить", 
                               command=self.clear_text, bg='#f44336', fg='white',
                               font=('Arial', 12, 'bold'), padx=20, pady=5)
        clear_button.pack(side='left', padx=5)
        
        # Результат
        tk.Label(self.root, text="Результат парсинга:", font=('Arial', 12, 'bold')).pack(anchor='w', padx=10, pady=(20,0))
        self.result_text = scrolledtext.ScrolledText(self.root, height=8, width=90, state='disabled')
        self.result_text.pack(padx=10, pady=5, fill='both')
    
    def parse_message(self):
        """Парсинг введенного сообщения"""
        text = self.text_input.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("Предупреждение", "Введите текст сообщения")
            return
        
        # Парсинг
        property_listing = self.parser.parse_property_message(text)
        
        # Показ результата
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        
        if property_listing:
            result = f"""✅ СООБЩЕНИЕ УСПЕШНО РАСПОЗНАНО

🏠 Название: {property_listing.title}
📍 Адрес: {property_listing.address}
💰 Цена: {property_listing.price}
🛏️ Спальни: {property_listing.bedrooms}
👤 Пользователь: {property_listing.user}
🔗 URL: {property_listing.url}

✨ Готово к отправке заявки!"""
            
            self.result_text.insert('1.0', result)
            
            # Предложение открыть в браузере
            if messagebox.askyesno("Открыть в браузере", 
                                 f"Объявление распознано!\n\nОткрыть ссылку в браузере?\n\n{property_listing.url}"):
                import webbrowser
                webbrowser.open(property_listing.url)
        else:
            result = """❌ СООБЩЕНИЕ НЕ РАСПОЗНАНО

Возможные причины:
• Неправильный формат сообщения
• Отсутствуют обязательные элементы (🏠, 📍, 💰, 🛏️, 🔗, 👤)
• Неправильная ссылка на daft.ie

Ожидаемый формат:
🏠 [Название]

📍 Адрес: [адрес]
💰 Цена: [цена]
🛏️ Спальни: [количество]

🔗 Посмотреть объявление (https://www.daft.ie/...)

👤 От пользователя: @username"""
            
            self.result_text.insert('1.0', result)
        
        self.result_text.config(state='disabled')
    
    def clear_text(self):
        """Очистка полей"""
        self.text_input.delete('1.0', tk.END)
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', tk.END)
        self.result_text.config(state='disabled')
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🧪 Запуск тестового приложения парсера")
    print("📝 Это приложение поможет проверить корректность парсинга сообщений")
    
    app = TestApp()
    app.run()
