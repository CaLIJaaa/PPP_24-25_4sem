import heapq
from collections import Counter
import base64
from typing import Dict, Tuple, Optional

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text: str) -> Tuple[Optional[HuffmanNode], Dict[str, str]]:
    if not text:
        return None, {}

    frequency = Counter(text)
    priority_queue = [HuffmanNode(char, freq) for char, freq in frequency.items()]
    heapq.heapify(priority_queue)

    if not priority_queue: 
        return None, {}
        
    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(priority_queue, merged)
    
    if not priority_queue: 
        return None, {}

    root = priority_queue[0]
    codes: Dict[str, str] = {}
    
    if not root.left and not root.right: # Случай с одним уникальным символом
        if root.char is not None:
            codes[root.char] = "0"
        return root, codes

    def generate_codes(node: Optional[HuffmanNode], current_code: str):
        if node is None:
            return
        if node.char is not None:
            codes[node.char] = current_code
            return
        generate_codes(node.left, current_code + "0")
        generate_codes(node.right, current_code + "1")

    generate_codes(root, "")
    return root, codes

def huffman_encode(text: str, codes: Dict[str, str]) -> Tuple[str, int]:
    if not text or not codes:
        return "", 0
    encoded_text = "".join(codes[char] for char in text if char in codes)
    
    padding = 0
    if encoded_text:
        padding = 8 - (len(encoded_text) % 8)
        if padding == 8: 
            padding = 0
        encoded_text += "0" * padding
    else: # Если текст был, но не нашлось символов в codes
        return "", 0

    byte_array = bytearray()
    for i in range(0, len(encoded_text), 8):
        byte = encoded_text[i:i+8]
        byte_array.append(int(byte, 2))
    
    return base64.b64encode(byte_array).decode('utf-8'), padding

def huffman_decode(encoded_data: str, codes: Dict[str, str], padding: int) -> str:
    if not encoded_data or not codes:
        return ""
    try:
        byte_array = base64.b64decode(encoded_data.encode('utf-8'))
    except Exception:
        return "" # Ошибка декодирования base64
        
    encoded_text = ""
    for byte_val in byte_array:
        encoded_text += bin(byte_val)[2:].rjust(8, '0')

    if padding > 0 and len(encoded_text) > padding:
        encoded_text = encoded_text[:-padding]
    elif padding > 0 and len(encoded_text) <= padding:
        return "" # Некорректный padding

    decoded_text = ""
    current_code = ""
    reversed_codes = {v: k for k, v in codes.items()}
    
    for bit in encoded_text:
        current_code += bit
        if current_code in reversed_codes:
            decoded_text += reversed_codes[current_code]
            current_code = ""
    
    if current_code and current_code in reversed_codes: # Проверка остатка
         decoded_text += reversed_codes[current_code]
    elif current_code: # Если остался незавершенный код
        pass # Можно логировать ошибку или возвращать частичный результат/ошибку
        
    return decoded_text

def xor_cipher(data_bytes: bytes, key: str) -> bytes:
    key_bytes = key.encode('utf-8')
    key_len = len(key_bytes)
    if not key_len: # Пустой ключ не шифрует
        return data_bytes
    return bytes([data_bytes[i] ^ key_bytes[i % key_len] for i in range(len(data_bytes))])

def xor_decipher(ciphered_bytes: bytes, key: str) -> bytes:
    return xor_cipher(ciphered_bytes, key) # XOR обратим

# Эти функции будут вызываться задачами Celery
# Они возвращают результат напрямую, а не task_id

def perform_encode(text: str, key: str, task_id: str, send_progress_update) -> Dict:
    if not text:
        send_progress_update(task_id, "encode", 100)
        return {"encoded_data": "", "key": key, "huffman_codes": {}, "padding": 0}

    send_progress_update(task_id, "encode", 10) # 1. Начало
    _, huffman_codes = build_huffman_tree(text)
    send_progress_update(task_id, "encode", 30) # 2. Дерево построено

    huffman_encoded_str, padding = huffman_encode(text, huffman_codes)
    send_progress_update(task_id, "encode", 60) # 3. Хаффман кодирование завершено

    if not huffman_encoded_str:
        send_progress_update(task_id, "encode", 100)
        return {"encoded_data": "", "key": key, "huffman_codes": huffman_codes, "padding": 0}

    huffman_encoded_bytes = base64.b64decode(huffman_encoded_str.encode('utf-8'))
    send_progress_update(task_id, "encode", 80) # 4. Декодировано из Base64 для XOR
    
    xor_ciphered_bytes = xor_cipher(huffman_encoded_bytes, key)
    final_encoded_data = base64.b64encode(xor_ciphered_bytes).decode('utf-8')
    send_progress_update(task_id, "encode", 100) # 5. Готово
    
    return {
        "encoded_data": final_encoded_data,
        "key": key, # Возвращаем ключ для информации
        "huffman_codes": huffman_codes,
        "padding": padding
    }

def perform_decode(encoded_data: str, key: str, huffman_codes: Dict[str, str], padding: int, task_id: str, send_progress_update) -> Dict:
    if not encoded_data:
        send_progress_update(task_id, "decode", 100)
        return {"decoded_text": ""}

    send_progress_update(task_id, "decode", 10) # 1. Начало
    try:
        ciphered_bytes = base64.b64decode(encoded_data.encode('utf-8'))
    except Exception as e:
        # Здесь можно логировать ошибку e
        send_progress_update(task_id, "decode", 100) 
        raise ValueError(f"Invalid base64 data for task {task_id}")
        
    send_progress_update(task_id, "decode", 30) # 2. Декодировано из Base64

    xor_deciphered_bytes = xor_decipher(ciphered_bytes, key)
    send_progress_update(task_id, "decode", 60) # 3. XOR расшифровка
    
    # Для huffman_decode, данные должны быть снова в base64
    xor_deciphered_base64_str = base64.b64encode(xor_deciphered_bytes).decode('utf-8')
    send_progress_update(task_id, "decode", 80) # 4. Подготовлено для Хаффмана

    decoded_text = huffman_decode(xor_deciphered_base64_str, huffman_codes, padding)
    send_progress_update(task_id, "decode", 100) # 5. Готово

    return {"decoded_text": decoded_text} 