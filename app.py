

def init_session_state(uid: str):
    keys = ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']
    defaults = {
        'fragments': [],
        'ref_map': {},
        'ref_counter': 1,
        'final_text': '',
        'final_refs': []
    }
    for k in keys:
        key_name = f"{uid}_{k}"
        if key_name not in st.session_state:
            st.session_state[key_name] = defaults[k]
    # начальный глобальный индекс
    if f"{uid}_start_index" not in st.session_state:
        st.session_state[f"{uid}_start_index"] = 1
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = None
    if 'restored' not in st.session_state:
        st.session_state.restored = False


# --- Восстановление автосэйва ---

def restore_autosave(uid: str):
    if not st.session_state.restored and os.path.exists(AUTOSAVE_FILE):
        data = load_project(AUTOSAVE_FILE)
        for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']:
            key_name = f"{uid}_{k}"
            st.session_state[key_name] = data.get(k, st.session_state[key_name])
        st.session_state.restored = True
        st.success('✅ Восстановлен последний проект из локального файла')


# --- Обновление автосэйва ---

def update_autosave(uid: str):
    data = {k: st.session_state[f"{uid}_{k}"] for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']}
    autosave_project(data)


# --- Основная функция ---
def main():
    st.set_page_config(page_title='Объединение ссылок по ГОСТ', layout='wide')

    # Sidebar: управление проектами
    st.sidebar.title('📁 Управление проектами')
    uid = st.sidebar.text_input('Ваше имя', value='user')
    init_session_state(uid)
    restore_autosave(uid)

    # выбор существующего проекта или дефолт
    projects = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.json')]
    selected = st.sidebar.selectbox('Выбрать проект', ['—'] + projects)
    project_path = os.path.join(PROJECT_DIR, selected) if selected != '—' else os.path.join(PROJECT_DIR, f"default.json")

    # Кнопки управления проектом
    if st.sidebar.button('💾 Сохранить проект'):
        save_project(project_path, {k: st.session_state[f"{uid}_{k}"] for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']})
        st.sidebar.success(f'Проект сохранён: {os.path.basename(project_path)}')

    if st.sidebar.button('📂 Загрузить проект'):
        if os.path.exists(project_path):
            data = load_project(project_path)
            for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']:
                st.session_state[f"{uid}_{k}"] = data.get(k, st.session_state[f"{uid}_{k}"])
            st.sidebar.success(f'Проект загружен: {os.path.basename(project_path)}')
        else:
            st.sidebar.error('Файл проекта не найден')

    if st.sidebar.button('🗑 Удалить проект'):
        if os.path.exists(project_path):
            os.remove(project_path)
            st.sidebar.success(f'Проект удалён: {os.path.basename(project_path)}')
        else:
            st.sidebar.error('Файл проекта не найден')

    uploaded = st.sidebar.file_uploader('Импорт из JSON', type='json')
    if uploaded is not None:
        try:
            data = json.load(uploaded)
            for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']:
                st.session_state[f"{uid}_{k}"] = data.get(k, st.session_state[f"{uid}_{k}"])
            st.sidebar.success('Импорт выполнен')
        except Exception as e:
            st.sidebar.error(f'Ошибка импорта: {e}')

    st.sidebar.markdown('---')
    st.sidebar.number_input('Начальный номер глобальной нумерации', min_value=1, key=f"{uid}_start_index")

    # JS: автозагрузка и автосохранение в браузере
    inject_autoload_receiver(uid)
    autoload_from_localstorage(uid)
    raw_js = load_from_localstorage_with_js_eval(uid)
    if raw_js:
        try:
            payload = json.loads(raw_js)
            for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']:
                st.session_state[f"{uid}_{k}"] = payload.get(k, st.session_state[f"{uid}_{k}"])
            st.success('✅ Восстановлено из LocalStorage')
        except Exception as e:
            st.warning(f'Ошибка восстановления из LocalStorage: {e}')

    st.title('Объединение ссылок (ГОСТ)')

    # Просмотр добавленных фрагментов
    st.subheader('Добавленные фрагменты')
    for i, frag in enumerate(st.session_state[f"{uid}_fragments"]):
        with st.expander(f'Фрагмент {i+1}', expanded=False):
            st.text_area('Текст', frag['text'], disabled=True, height=150)
            st.markdown('**Список литературы:**')
            for num, txt in frag['refs'].items():
                st.write(f'{num}. {txt}')
            cols = st.columns([0.2, 0.2, 0.2, 0.4])
            if cols[0].button('⬆️', key=f'up_{i}') and i > 0:
                lst = st.session_state[f"{uid}_fragments"]
                lst[i-1], lst[i] = lst[i], lst[i-1]
                st.experimental_rerun()
            if cols[1].button('⬇️', key=f'down_{i}') and i < len(st.session_state[f"{uid}_fragments"]) - 1:
                lst = st.session_state[f"{uid}_fragments"]
                lst[i+1], lst[i] = lst[i], lst[i+1]
                st.experimental_rerun()
            if cols[2].button('✏️', key=f'edit_{i}'):
                st.session_state.edit_index = i
                st.experimental_rerun()
            if cols[3].button('🗑', key=f'del_{i}'):
                st.session_state[f"{uid}_fragments"].pop(i)
                st.experimental_rerun()
```
# -*- coding: utf-8 -*-
import os
import json
import re
import logging
from io import BytesIO

import streamlit as st
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval
from docx import Document
from docx.shared import Pt
from docx.oxml.ns import qn
from rapidfuzz import fuzz

# Логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Константы
PROJECT_DIR = "projects"
AUTOSAVE_FILE = "project_autosave.json"
if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)

# Регулярные выражения
REFS_SPLIT_REGEX = re.compile(
    r"(?=^\s*(?:\[\d+\]|(?:19|20)\d{2}\.|[A-ZА-ЯЁ][a-zа-яё]+,|\d+\.))",
    flags=re.M
)
CITE_REGEX = re.compile(r"\[(\d+)\]")

# --- Функции для автозагрузки через localStorage и JS EVAL ---

def inject_autoload_receiver(user_id: str):
    js = f"""
    <script>
    window.addEventListener('message', event => {{
        if (event.data?.type === 'gost-autoload') {{
            const payload = event.data.payload;
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'gost_autoload_data';
            input.value = JSON.stringify(payload);
            document.body.appendChild(input);
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    }});
    </script>
    """
    components.html(js, height=0)


def autoload_from_localstorage(user_id: str):
    js = f"""
    <script>
    const data = localStorage.getItem('autosave_{user_id}');
    if (data) window.postMessage({{ type: 'gost-autoload', payload: JSON.parse(data) }}, '*');
    </script>
    """
    components.html(js, height=0)


def load_from_localstorage_with_js_eval(user_id: str) -> str:
    key = f"autosave_{user_id}"
    return streamlit_js_eval(js_expressions=f"localStorage.getItem('{key}')", key="read_localstorage")

# --- Работа с проектом и автосохранение ---

def save_project(project_path: str, data: dict):
    try:
        with open(project_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения проекта: {e}")


def load_project(project_path: str) -> dict:
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Ошибка загрузки проекта: {e}")
        return {}


def autosave_project(data: dict):
    try:
        with open(AUTOSAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка автосохранения проекта: {e}")

# --- Парсинг списка литературы ---

def parse_references(refs_text: str) -> dict:
    parts = [s.strip() for s in re.split(r"(?=^\s*\[?\d+\]?\.?)", refs_text.strip(), flags=re.M) if s.strip()]
    refs = {}
    for idx, p in enumerate(parts, start=1):
        text = re.sub(r"^\[?\d+\]?\.?", '', p).strip()
        if text:
            refs[idx] = text
    return refs

# --- Обработка фрагмента ---

def process_fragment(frag: dict, global_map: dict, counter: list) -> tuple:
    local_list = [v for _, v in sorted(frag['refs'].items(), key=lambda x: int(x[0]))]

    def replace_cite(match: re.Match) -> str:
        num = int(match.group(1))
        if 1 <= num <= len(local_list):
            ref_text = local_list[num - 1]
            for known in global_map:
                if fuzz.ratio(known.lower(), ref_text.lower()) >= 90:
                    return f"[{global_map[known]}]"
            global_map[ref_text] = counter[0]
            counter[0] += 1
            return f"[{global_map[ref_text]}]"
        logging.warning(f"Номер ссылки [{num}] вне диапазона списка литературы")
        return '[??]'

    text = re.sub(CITE_REGEX, replace_cite, frag['text'])
    return text, global_map, counter

# --- Генерация DOCX ---

def generate_docx(text: str, references: list) -> Document:
    doc = Document()
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(12)
    for para in text.strip().split('\n'):
        doc.add_paragraph(para)
    doc.add_paragraph('Список литературы:')
    for ref in references:
        doc.add_paragraph(ref, style='List Number')
    return doc

# --- Инициализация состояния сессии ---

def init_session_state(uid: str):
    keys = ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']
    defaults = {
        'fragments': [],
        'ref_map': {},
        'ref_counter': 1,
        'final_text': '',
        'final_refs': []
    }
    for k in keys:
        key = f"{uid}_{k}"
        if key not in st.session_state:
            st.session_state[key] = defaults[k]
    if f"{uid}_start_index" not in st.session_state:
        st.session_state[f"{uid}_start_index"] = 1
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = None
    if 'restored' not in st.session_state:
        st.session_state.restored = False


def restore_autosave(uid: str):
    if not st.session_state.restored and os.path.exists(AUTOSAVE_FILE):
        data = load_project(AUTOSAVE_FILE)
        for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']:
            st.session_state[f"{uid}_{k}"] = data.get(k, st.session_state[f"{uid}_{k}"])
        st.session_state.restored = True
        st.success('✅ Восстановлен последний проект')


def update_autosave(uid: str):
    data = {k: st.session_state[f"{uid}_{k}"] for k in ['fragments', 'ref_map', 'ref_counter', 'final_text', 'final_refs']}
    autosave_project(data)

# --- Основная функция ---

def main():
    st.set_page_config(page_title='Объединение ссылок по ГОСТ', layout='wide')

    # Sidebar
    st.sidebar.title('📁 Управление проектами')
    uid = st.sidebar.text_input('Ваше имя', value='user')
    init_session_state(uid)
    restore_autosave(uid)
    projects = [f for f in os.listdir(PROJECT_DIR) if f.endswith('.json')]
    selected = st.sidebar.selectbox('Выбрать проект', ['—'] + projects)
    project_path = os.path.join(PROJECT_DIR, selected) if selected != '—' else os.path.join(PROJECT_DIR, f"default.json")

    if st.sidebar.button('💾 Сохранить проект'):
        save_project(project_path, {k: st.session_state[f"{uid}_{k}"] for k in ['fragments','ref_map','ref_counter','final_text','final_refs']})
        st.sidebar.success(f'Проект сохранён: {os.path.basename(project_path)}')
    if st.sidebar.button('📂 Загрузить проект') and os.path.exists(project_path):
        data = load_project(project_path)
        for k in ['fragments','ref_map','ref_counter','final_text','final_refs']:
            st.session_state[f"{uid}_{k}"] = data.get(k, st.session_state[f"{uid}_{k}"])
        st.sidebar.success(f'Проект загружен: {os.path.basename(project_path)}')
    if st.sidebar.button('🗑 Удалить проект') and os.path.exists(project_path):
        os.remove(project_path)
        st.sidebar.success(f'Проект удалён: {os.path.basename(project_path)}')
    uploaded = st.sidebar.file_uploader('Импорт из JSON', type='json')
    if uploaded:
        try:
            data = json.load(uploaded)
            for k in ['fragments','ref_map','ref_counter','final_text','final_refs']:
                st.session_state[f"{uid}_{k}"] = data.get(k, st.session_state[f"{uid}_{k}"])
            st.sidebar.success('Импорт выполнен')
        except Exception as e:
            st.sidebar.error(f'Ошибка импорта: {e}')
    st.sidebar.markdown('---')
    st.sidebar.number_input('Начальный номер глобальной нумерации', min_value=1, key=f"{uid}_start_index")

    # JS
    inject_autoload_receiver(uid)
    autoload_from_localstorage(uid)
    raw_js = load_from_localstorage_with_js_eval(uid)
    if raw_js:
        try:
            payload = json.loads(raw_js)
            for k in ['fragments','ref_map','ref_counter','final_text','final_refs']:
                st.session_state[f"{uid}_{k}"] = payload.get(k, st.session_state[f"{uid}_{k}"])
            st.success('✅ Восстановлено из LocalStorage')
        except Exception as e:
            st.warning(f'Ошибка восстановления из LocalStorage: {e}')

    # Main UI
    st.title('Объединение ссылок (ГОСТ)')
    st.subheader('Добавленные фрагменты')
    for i, frag in enumerate(st.session_state[f"{uid}_fragments"]):
        with st.expander(f'Фрагмент {i+1}'):
            st.text_area('Текст', frag['text'], disabled=True, height=150)
            st.markdown('**Список литературы:**')
            for num, ref in frag['refs'].items():
                st.write(f'{num}. {ref}')
            cols = st.columns([0.2,0.2,0.2,0.4])
            if cols[0].button('⬆️', key=f'up_{i}') and i>0:
                lst = st.session_state[f"{uid}_fragments"]; lst[i-1], lst[i] = lst[i], lst[i-1]; st.experimental_rerun()
            if cols[1].button('⬇️', key=f'down_{i}') and i < len(st.session_state[f"{uid}_fragments"]) - 1:
                lst = st.session_state[f"{uid}_fragments"]; lst[i+1], lst[i] = lst[i], lst[i+1]; st.experimental_rerun()
            if cols[2].button('✏️', key=f'edit_{i}'): st.session_state.edit_index = i; st.experimental_rerun()
            if cols[3].button('🗑', key=f'del_{i}'): st.session_state[f"{uid}_fragments"].pop(i); st.experimental_rerun()

    with st.form('fragment_form', clear_on_submit=True):
        default_text = ''
        default_refs = ''
        if st.session_state.edit_index is not None:
            frag = st.session_state[f"{uid}_fragments"][st.session_state.edit_index]
            default_text = frag['text']
            default_refs = '\n'.join(f"{num}. {txt}" for num, txt in frag['refs'].items())
        txt = st.text_area('Текст с [1]', value=default_text, height=200)
        refs = st.text_area('Список литературы', value=default_refs, height=200)
        if st.form_submit_button('💾 Сохранить фрагмент'):
            parsed = parse_references(refs)
            new_frag = {'text': txt, 'refs': parsed}
            if st.session_state.edit_index is not None:
                st.session_state[f"{uid}_fragments"][st.session_state.edit_index] = new_frag
                st.session_state.edit_index = None
            else:
                st.session_state[f"{uid}_fragments"].append(new_frag)
            update_autosave(uid)
            st.experimental_rerun()

    if st.button('📄 Объединить всё'):
        text_out = ''
        global_map = {}
        counter = [st.session_state.get(f"{uid}_start_index...
```
    if st.button('📄 Объединить всё'):
        # объединяем текст и переиндексируем ссылки
        text_out = ""
        global_map = {}
        counter = [st.session_state.get(f"{uid}_start_index", 1)]
        issues = []

        for idx, frag in enumerate(st.session_state[f"{uid}_fragments"]):
            # проверяем ссылки в тексте vs список литературы
            cited = set(int(n) for n in re.findall(CITE_REGEX, frag['text']))
            available = set(int(n) for n in frag['refs'].keys())
            missing = sorted(cited - available)
            extra = sorted(available - cited)
            if missing:
                issues.append(f"Фрагмент {idx+1}: ссылки {missing} нет в списке.")
            # заменяем локальные номера на глобальные
            processed, global_map, counter = process_fragment(frag, global_map, counter)
            text_out += processed + "\n\n"

        if issues:
            st.warning("Обнаружены несоответствия:")
            for msg in issues:
                st.markdown(f"- {msg}")

        # формируем итоговый список литературы
        refs_sorted = sorted(global_map.items(), key=lambda x: x[1])
        refs_out = [f"[{num}] {txt}" for txt, num in refs_sorted]

        # сохраняем в сессию
        st.session_state[f"{uid}_final_text"] = text_out
        st.session_state[f"{uid}_final_refs"] = refs_out
        update_autosave(uid)

        # выводим результат
        st.subheader("Результат объединения")
        st.code(text_out, language="markdown")
        st.subheader("Список литературы")
        for r in refs_out:
            st.markdown(r)

    # экспорт в DOCX
    if st.session_state.get(f"{uid}_final_text"):
        if st.button('📥 Скачать DOCX файл'):
            doc = generate_docx(
                st.session_state[f"{uid}_final_text"],
                st.session_state[f"{uid}_final_refs"]
            )
            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)
            st.download_button(
                label="Скачать DOCX",
                data=buf,
                file_name="merged_references.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

if __name__ == "__main__":
    main()
