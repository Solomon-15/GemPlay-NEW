// Утилиты для валидации и транслитерации имён пользователей
import { useState } from 'react';

// Карта для транслитерации кириллицы в латиницу
const TRANSLITERATION_MAP = {
  // Русские символы
  'а': 'a', 'А': 'A', 'б': 'b', 'Б': 'B', 'в': 'v', 'В': 'V', 'г': 'g', 'Г': 'G',
  'д': 'd', 'Д': 'D', 'е': 'e', 'Е': 'E', 'ё': 'yo', 'Ё': 'Yo', 'ж': 'zh', 'Ж': 'Zh',
  'з': 'z', 'З': 'Z', 'и': 'i', 'И': 'I', 'й': 'y', 'Й': 'Y', 'к': 'k', 'К': 'K',
  'л': 'l', 'Л': 'L', 'м': 'm', 'М': 'M', 'н': 'n', 'Н': 'N', 'о': 'o', 'О': 'O',
  'п': 'p', 'П': 'P', 'р': 'r', 'Р': 'R', 'с': 's', 'С': 'S', 'т': 't', 'Т': 'T',
  'у': 'u', 'У': 'U', 'ф': 'f', 'Ф': 'F', 'х': 'h', 'Х': 'H', 'ц': 'ts', 'Ц': 'Ts',
  'ч': 'ch', 'Ч': 'Ch', 'ш': 'sh', 'Ш': 'Sh', 'щ': 'sch', 'Щ': 'Sch', 'ъ': '', 'Ъ': '',
  'ы': 'y', 'Ы': 'Y', 'ь': '', 'Ь': '', 'э': 'e', 'Э': 'E', 'ю': 'yu', 'Ю': 'Yu',
  'я': 'ya', 'Я': 'Ya',
  
  // Казахские символы
  'ә': 'a', 'Ә': 'A', 'ғ': 'g', 'Ғ': 'G', 'қ': 'k', 'Қ': 'K', 'ң': 'ng', 'Ң': 'Ng',
  'ө': 'o', 'Ө': 'O', 'ұ': 'u', 'Ұ': 'U', 'ү': 'u', 'Ү': 'U', 'һ': 'h', 'Һ': 'H',
  'і': 'i', 'І': 'I',
  
  // Украинские символы
  'ї': 'yi', 'Ї': 'Yi', 'є': 'ye', 'Є': 'Ye', 'і': 'i', 'І': 'I', 'ґ': 'g', 'Ґ': 'G'
};

// Регулярные выражения для валидации
const LATIN_ONLY_REGEX = /^[a-zA-Z0-9\-_.]*$/;
const NON_LATIN_REGEX = /[^\x00-\x7F]/;
const CONSECUTIVE_UNDERSCORES_REGEX = /__+/;
const SPECIAL_CHARS_REGEX = /[!@#$%^&*()+=\[\]{}\\|;':"\/?,<>~`]/;
const TRIM_SPACES_REGEX = /^\s+|\s+$/;

/**
 * Проверяет, содержит ли строка только латинские символы
 * @param {string} text - Текст для проверки
 * @returns {boolean}
 */
export const isLatinOnly = (text) => {
  return LATIN_ONLY_REGEX.test(text);
};

/**
 * Транслитерация кириллицы в латиницу
 * @param {string} text - Текст для транслитерации
 * @returns {string}
 */
export const transliterateToLatin = (text) => {
  return text
    .split('')
    .map(char => TRANSLITERATION_MAP[char] || char)
    .join('');
};

/**
 * Удаляет недопустимые символы из имени пользователя
 * @param {string} username - Имя пользователя
 * @returns {string}
 */
export const sanitizeUsername = (username) => {
  let sanitized = username;
  
  // Транслитерируем кириллицу
  if (NON_LATIN_REGEX.test(sanitized)) {
    sanitized = transliterateToLatin(sanitized);
  }
  
  // Удаляем специальные символы (кроме разрешенных)
  sanitized = sanitized.replace(SPECIAL_CHARS_REGEX, '');
  
  // Заменяем множественные подчёркивания на одиночные
  sanitized = sanitized.replace(CONSECUTIVE_UNDERSCORES_REGEX, '_');
  
  // Убираем пробелы в начале и конце
  sanitized = sanitized.replace(TRIM_SPACES_REGEX, '');
  
  return sanitized;
};

/**
 * Проверяет имя пользователя на валидность
 * @param {string} username - Имя пользователя
 * @returns {object} - Результат валидации
 */
export const validateUsername = (username) => {
  const errors = [];
  
  // Проверка длины
  if (!username || username.length < 3) {
    errors.push('Минимальная длина имени - 3 символа');
  }
  
  if (username && username.length > 15) {
    errors.push('Максимальная длина имени - 15 символов');
  }
  
  // Проверка на пустую строку или только пробелы
  if (!username || !username.trim()) {
    errors.push('Имя пользователя не может быть пустым');
  }
  
  // Проверка на нелатинские символы
  if (username && NON_LATIN_REGEX.test(username)) {
    errors.push('Имя должно содержать только латинские символы');
  }
  
  // Проверка на недопустимые символы
  if (username && SPECIAL_CHARS_REGEX.test(username)) {
    errors.push('Недопустимые символы. Разрешены: буквы, цифры, дефис, подчёркивание, точка, пробелы');
  }
  
  // Проверка на подряд идущие подчёркивания
  if (username && CONSECUTIVE_UNDERSCORES_REGEX.test(username)) {
    errors.push('Недопустимы подряд идущие символы подчёркивания');
  }
  
  // Проверка на пробелы в начале и конце
  if (username && TRIM_SPACES_REGEX.test(username)) {
    errors.push('Пробелы в начале и конце имени недопустимы');
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    sanitized: sanitizeUsername(username)
  };
};

/**
 * Обработчик изменения поля ввода имени пользователя (для React)
 * @param {string} value - Новое значение
 * @param {function} setValue - Функция для установки значения
 * @param {function} setError - Функция для установки ошибки (опционально)
 * @returns {string} - Обработанное значение
 */
export const handleUsernameInput = (value, setValue, setError) => {
  // Блокируем ввод нелатинских символов
  let processedValue = value;
  
  // Если есть нелатинские символы, транслитерируем их
  if (NON_LATIN_REGEX.test(processedValue)) {
    processedValue = transliterateToLatin(processedValue);
  }
  
  // Удаляем недопустимые символы
  processedValue = processedValue.replace(SPECIAL_CHARS_REGEX, '');
  
  // Предотвращаем множественные подчёркивания
  processedValue = processedValue.replace(CONSECUTIVE_UNDERSCORES_REGEX, '_');
  
  // Ограничиваем длину
  if (processedValue.length > 15) {
    processedValue = processedValue.substring(0, 15);
  }
  
  // Обновляем значение
  setValue(processedValue);
  
  // Валидируем и показываем ошибки
  if (setError) {
    const validation = validateUsername(processedValue);
    if (!validation.isValid && processedValue.length > 0) {
      setError(validation.errors[0]);
    } else {
      setError('');
    }
  }
  
  return processedValue;
};

/**
 * Хук для валидации имени пользователя в реальном времени
 * @param {string} initialValue - Начальное значение
 * @returns {object} - Объект с данными и функциями
 */
export const useUsernameValidation = (initialValue = '') => {
  const [username, setUsername] = useState(sanitizeUsername(initialValue));
  const [error, setError] = useState('');
  const [isValid, setIsValid] = useState(false);
  
  const handleChange = (value) => {
    const processedValue = handleUsernameInput(value, setUsername, setError);
    const validation = validateUsername(processedValue);
    setIsValid(validation.isValid);
    return processedValue;
  };
  
  return {
    username,
    error,
    isValid,
    handleChange,
    setUsername: (value) => {
      const sanitized = sanitizeUsername(value);
      setUsername(sanitized);
      const validation = validateUsername(sanitized);
      setIsValid(validation.isValid);
      setError(validation.isValid ? '' : validation.errors[0] || '');
    }
  };
};

export default {
  isLatinOnly,
  transliterateToLatin,
  sanitizeUsername,
  validateUsername,
  handleUsernameInput,
  useUsernameValidation
};