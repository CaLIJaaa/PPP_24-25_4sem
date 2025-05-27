import heapq
from collections import Counter, defaultdict
import base64
from typing import Dict

class HuffmanNode:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text):
    if not text:
        return None, {}

    frequency = Counter(text)
    priority_queue = [HuffmanNode(char, freq) for char, freq in frequency.items()]
    heapq.heapify(priority_queue)

    if not priority_queue: # Случай пустого текста или текста с одним уникальным символом обработан не полностью
        return None, {}
        
    while len(priority_queue) > 1:
        left = heapq.heappop(priority_queue)
        right = heapq.heappop(priority_queue)
        merged = HuffmanNode(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(priority_queue, merged)
    
    if not priority_queue: # Добавил проверку на случай если priority_queue пуста
        return None, {}

    root = priority_queue[0]
    codes = {}
    
    # Для случая с одним уникальным символом
    if not root.left and not root.right:
        codes[root.char] = "0"
        return root, codes

    def generate_codes(node, current_code):
        if node is None:
            return
        if node.char is not None:
            codes[node.char] = current_code
            return
        generate_codes(node.left, current_code + "0")
        generate_codes(node.right, current_code + "1")

    generate_codes(root, "")
    return root, codes

def huffman_encode(text, codes):
    if not text or not codes:
        return "", 0
    encoded_text = "".join(codes[char] for char in text)
    
    padding = 0
    # Если codes пуст или text пуст, encoded_text будет пустым, дальнейшие действия приведут к ошибке.
    if encoded_text:
        padding = 8 - (len(encoded_text) % 8)
        if padding == 8: # если длина кратна 8, то padding не нужен
            padding = 0
        encoded_text += "0" * padding
    
    byte_array = bytearray()
    # Если encoded_text пуст, то этот цикл не выполнится
    for i in range(0, len(encoded_text), 8):
        byte = encoded_text[i:i+8]
        byte_array.append(int(byte, 2))
    
    return base64.b64encode(byte_array).decode('utf-8'), padding

def huffman_decode(encoded_data, codes, padding):
    if not encoded_data or not codes:
        return ""

    byte_array = base64.b64decode(encoded_data.encode('utf-8'))
    encoded_text = ""
    for byte in byte_array:
        encoded_text += bin(byte)[2:].rjust(8, '0')

    if padding > 0:
        encoded_text = encoded_text[:-padding]

    decoded_text = ""
    current_code = ""
    # Поменяем codes местами ключ-значение для удобства декодирования
    reversed_codes = {v: k for k, v in codes.items()}
    
    for bit in encoded_text:
        current_code += bit
        if current_code in reversed_codes:
            decoded_text += reversed_codes[current_code]
            current_code = ""
    return decoded_text

def xor_cipher(text_bytes, key):
    key_bytes = key.encode('utf-8')
    key_len = len(key_bytes)
    return bytes([text_bytes[i] ^ key_bytes[i % key_len] for i in range(len(text_bytes))])

def xor_decipher(ciphered_bytes, key):
    # XOR расшифровка идентична шифрованию
    return xor_cipher(ciphered_bytes, key)

def encode_text(text: str, key: str):
    if not text: # Обработка пустого текста
        return "", key, {}, 0

    _, huffman_codes = build_huffman_tree(text)
    # Если huffman_codes пуст (например, для пустого текста), то huffman_encode вернет ("", 0)
    huffman_encoded_str, padding = huffman_encode(text, huffman_codes)

    # huffman_encoded_str - это base64 строка, ее нужно декодировать перед XOR
    if not huffman_encoded_str: # Если строка пустая, нет смысла продолжать
         return "", key, huffman_codes, 0

    # Декодируем из base64 перед XOR
    huffman_encoded_bytes = base64.b64decode(huffman_encoded_str.encode('utf-8'))
    
    xor_ciphered_bytes = xor_cipher(huffman_encoded_bytes, key)
    
    # Кодируем результат XOR обратно в base64 для ответа
    final_encoded_data = base64.b64encode(xor_ciphered_bytes).decode('utf-8')
    
    return final_encoded_data, key, huffman_codes, padding

def decode_text(encoded_data: str, key: str, huffman_codes: Dict[str, str], padding: int):
    if not encoded_data: # Обработка пустых данных
        return ""

    # Декодируем из base64 перед XOR
    ciphered_bytes = base64.b64decode(encoded_data.encode('utf-8'))
    
    xor_deciphered_bytes = xor_decipher(ciphered_bytes, key)

    # Кодируем результат XOR обратно в base64, т.к. huffman_decode ожидает base64 строку
    xor_deciphered_base64_str = base64.b64encode(xor_deciphered_bytes).decode('utf-8')
    
    # Если huffman_codes пуст, huffman_decode вернет ""
    decoded_text = huffman_decode(xor_deciphered_base64_str, huffman_codes, padding)
    return decoded_text 