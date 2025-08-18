"""
Утилиты для валидации и транслитерации имён пользователей
"""

import re
from typing import Dict, List, Tuple

# Карта транслитерации кириллицы в латиницу
TRANSLITERATION_MAP = {
    # Русские символы
    'а': 'a', 'А': 'A', 'б': 'b', 'Б': 'B', 'в': 'v', 'В': 'V', 'г': 'g', 'Г': 'G',
    'д': 'd', 'Д': 'D', 'е': 'e', 'Е': 'E', 'ё': 'yo', 'Ё': 'Yo', 'ж': 'zh', 'Ж': 'Zh',
    'з': 'z', 'З': 'Z', 'и': 'i', 'И': 'I', 'й': 'y', 'Й': 'Y', 'к': 'k', 'К': 'K',
    'л': 'l', 'Л': 'L', 'м': 'm', 'М': 'M', 'н': 'n', 'Н': 'N', 'о': 'o', 'О': 'O',
    'п': 'p', 'П': 'P', 'р': 'r', 'Р': 'R', 'с': 's', 'С': 'S', 'т': 't', 'Т': 'T',
    'у': 'u', 'У': 'U', 'ф': 'f', 'Ф': 'F', 'х': 'h', 'Х': 'H', 'ц': 'ts', 'Ц': 'Ts',
    'ч': 'ch', 'Ч': 'Ch', 'ш': 'sh', 'Ш': 'Sh', 'щ': 'sch', 'Щ': 'Sch', 'ъ': '', 'Ъ': '',
    'ы': 'y', 'Ы': 'Y', 'ь': '', 'Ь': '', 'э': 'e', 'Э': 'E', 'ю': 'yu', 'Ю': 'Yu',
    'я': 'ya', 'Я': 'Ya',
    
    # Казахские символы
    'ә': 'a', 'Ә': 'A', 'ғ': 'g', 'Ғ': 'G', 'қ': 'k', 'Қ': 'K', 'ң': 'ng', 'Ң': 'Ng',
    'ө': 'o', 'Ө': 'O', 'ұ': 'u', 'Ұ': 'U', 'ү': 'u', 'Ү': 'U', 'һ': 'h', 'Һ': 'H',
    'і': 'i', 'І': 'I',
    
    # Украинские символы
    'ї': 'yi', 'Ї': 'Yi', 'є': 'ye', 'Є': 'Ye', 'і': 'i', 'І': 'I', 'ґ': 'g', 'Ґ': 'G'
}

# Регулярные выражения для валидации
LATIN_ONLY_REGEX = re.compile(r'^[a-zA-Z0-9\-_. ]*$')
NON_LATIN_REGEX = re.compile(r'[^\x00-\x7F]')
CONSECUTIVE_UNDERSCORES_REGEX = re.compile(r'__+')
SPECIAL_CHARS_REGEX = re.compile(r'[!@#$%^&*()+=\[\]{}\\|;\':"\/?,<>~`]')
TRIM_SPACES_REGEX = re.compile(r'^\s+|\s+$')

def is_latin_only(text: str) -> bool:
    """Проверяет, содержит ли строка только латинские символы"""
    return bool(LATIN_ONLY_REGEX.match(text))

def transliterate_to_latin(text: str) -> str:
    """Транслитерация кириллицы в латиницу"""
    result = []
    for char in text:
        if char in TRANSLITERATION_MAP:
            result.append(TRANSLITERATION_MAP[char])
        else:
            result.append(char)
    return ''.join(result)

def sanitize_username(username: str) -> str:
    """Очищает имя пользователя от недопустимых символов"""
    if not username:
        return ""
    
    # Транслитерируем кириллицу
    if NON_LATIN_REGEX.search(username):
        username = transliterate_to_latin(username)
    
    # Удаляем специальные символы (кроме разрешенных)
    username = SPECIAL_CHARS_REGEX.sub('', username)
    
    # Заменяем множественные подчёркивания на одиночные
    username = CONSECUTIVE_UNDERSCORES_REGEX.sub('_', username)
    
    # Убираем пробелы в начале и конце
    username = username.strip()
    
    return username

def validate_username(username: str) -> Tuple[bool, List[str]]:
    """
    Валидирует имя пользователя
    Возвращает: (is_valid, list_of_errors)
    """
    errors = []
    
    if not username:
        errors.append("Имя пользователя не может быть пустым")
        return False, errors
    
    # Проверка длины
    if len(username) < 3:
        errors.append("Минимальная длина имени - 3 символа")
    
    if len(username) > 15:
        errors.append("Максимальная длина имени - 15 символов")
    
    # Проверка на только пробелы
    if not username.strip():
        errors.append("Имя пользователя не может состоять только из пробелов")
    
    # Проверка на нелатинские символы
    if NON_LATIN_REGEX.search(username):
        errors.append("Имя должно содержать только латинские символы")
    
    # Проверка на недопустимые символы
    if SPECIAL_CHARS_REGEX.search(username):
        errors.append("Недопустимые символы. Разрешены: буквы, цифры, дефис, подчёркивание, точка, пробелы")
    
    # Проверка на подряд идущие подчёркивания
    if CONSECUTIVE_UNDERSCORES_REGEX.search(username):
        errors.append("Недопустимы подряд идущие символы подчёркивания")
    
    # Проверка на пробелы в начале и конце
    if username != username.strip():
        errors.append("Пробелы в начале и конце имени недопустимы")
    
    return len(errors) == 0, errors

def process_username(username: str) -> Dict[str, any]:
    """
    Обрабатывает имя пользователя: валидирует и очищает
    Возвращает словарь с результатами обработки
    """
    if not username:
        return {
            'original': username,
            'sanitized': '',
            'is_valid': False,
            'errors': ['Имя пользователя не может быть пустым'],
            'changed': False
        }
    
    sanitized = sanitize_username(username)
    is_valid, errors = validate_username(sanitized)
    changed = username != sanitized
    
    return {
        'original': username,
        'sanitized': sanitized,
        'is_valid': is_valid,
        'errors': errors,
        'changed': changed
    }

def get_username_suggestions(username: str, count: int = 3) -> List[str]:
    """Генерирует предложения для имени пользователя если оно невалидно"""
    base = sanitize_username(username)
    if not base:
        base = "user"
    
    # Обрезаем до максимальной длины
    if len(base) > 10:  # Оставляем место для суффикса
        base = base[:10]
    
    suggestions = []
    
    # Добавляем числа
    for i in range(1, count + 1):
        suggestion = f"{base}{i}"
        if len(suggestion) <= 15:
            suggestions.append(suggestion)
    
    # Добавляем случайные постфиксы
    postfixes = ["_pro", "_gamer", "_player"]
    for postfix in postfixes[:count - len(suggestions)]:
        suggestion = f"{base}{postfix}"
        if len(suggestion) <= 15:
            suggestions.append(suggestion)
    
    return suggestions[:count]