# Объединение ссылок по ГОСТ

Веб-приложение на Streamlit для вставки текста с локальными ссылками ([1], [2]...) и соответствующего списка литературы.
Автоматически объединяет фрагменты, устраняет дубликаты, подсвечивает ошибки и экспортирует результат в DOCX.

## 🚀 Как развернуть на Streamlit Cloud

1. Создайте аккаунт на https://streamlit.io/cloud и залогиньтесь
2. Создайте репозиторий на GitHub и загрузите в него следующие файлы:
   - `app.py`
   - `requirements.txt`
3. Перейдите на https://streamlit.io/cloud, выберите "New app", подключите ваш GitHub репозиторий
4. Нажмите "Deploy" — и приложение станет доступно онлайн!

## 🧾 Требуемые библиотеки

Указаны в `requirements.txt`:
- streamlit
- python-docx
- rapidfuzz

## 📁 Возможности

- Поддержка разных стилей ссылок и списков литературы (англ/рус)
- Подсветка ошибок ссылок
- Валидация ссылок перед сохранением
- Сортировка/перемещение/удаление/редактирование фрагментов
- Объединение и экспорт результата в DOCX