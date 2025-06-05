# client.py
import asyncio
import websockets
import json
import uuid
import httpx

# Глобальная переменная для хранения активного WebSocket соединения
current_websocket: websockets.WebSocketClientProtocol | None = None
current_client_id: str | None = None

# URL FastAPI сервера
BASE_API_URL = "http://localhost:8000/encryption"

async def listen_to_websocket(websocket: websockets.WebSocketClientProtocol, client_id: str):
    print(f"[WS Listener for {client_id}] Ожидание сообщений...")
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"\n[Сообщение от сервера для {client_id}]:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(f"\n[Не JSON сообщение от сервера для {client_id}]: {message}")
            print(f"\nclient@{client_id}> ", end="", flush=True)
    except websockets.exceptions.ConnectionClosed as e:
        print(f"\n[WS Listener for {client_id}] Соединение закрыто штатно: {e.reason} (код: {e.code})")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"\n[WS Listener for {client_id}] Соединение закрыто с ошибкой: {e.reason} (код: {e.code})")
    except Exception as e:
        print(f"\n[WS Listener for {client_id}] Ошибка в цикле прослушивания: {type(e).__name__}: {e}")
    finally:
        print(f"\n[WS Listener for {client_id}] Прослушивание завершено.")
        global current_websocket
        if websocket == current_websocket:
            current_websocket = None

async def connect_command(client_id_to_connect: str):
    global current_websocket
    global current_client_id

    if current_websocket:
        print(f"Уже есть активное WebSocket соединение или была попытка с {current_client_id}. Сначала отключитесь (`disconnect`).")
        return

    ws_uri = f"ws://localhost:8000/encryption/ws/{client_id_to_connect}"
    try:
        print(f"Подключение к {ws_uri}...")
        websocket = await websockets.connect(ws_uri)
        current_websocket = websocket
        current_client_id = client_id_to_connect
        print(f"Успешно подключено к WebSocket для client_id: {client_id_to_connect}")
        asyncio.create_task(listen_to_websocket(websocket, client_id_to_connect))
    except Exception as e:
        print(f"Не удалось подключиться к WebSocket: {type(e).__name__}: {e}")
        current_websocket = None

async def disconnect_command():
    global current_websocket
    if current_websocket:
        print(f"Отключение от WebSocket для client_id: {current_client_id}...")
        try:
            await current_websocket.close()
            print("Соединение WebSocket закрыто.")
        except Exception as e:
            print(f"Ошибка при закрытии WebSocket: {type(e).__name__}: {e}")
        current_websocket = None
    else:
        print("Нет активного WebSocket соединения для отключения.")

def print_help():
    print("\nДоступные команды:")
    print("  connect [client_id]     - Подключиться к WebSocket. client_id генерируется, если не указан.")
    print("  encode <key> <text>   - Отправить задачу кодирования (нужен активный client_id).")
    print("  decode <key> <pad> <b64_data> \"<json_codes>\" - Отправить задачу декодирования.")
    print("                            (pad - padding, json_codes - строка в двойных кавычках)")
    print("  disconnect              - Отключиться от WebSocket.")
    print("  help                    - Показать это сообщение.")
    print("  exit                    - Выйти из клиента.")

async def send_encode_request(client_id: str, key: str, text: str):
    url = f"{BASE_API_URL}/encode/{client_id}"
    payload = {"text": text, "key": key}
    print(f"\nОтправка запроса на кодирование: {url} с телом: {payload}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            result = response.json()
            print(f"Ответ от сервера (encode task): {json.dumps(result, indent=2, ensure_ascii=False)}")
    except httpx.HTTPStatusError as e:
        print(f"Ошибка HTTP Status (encode): {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"Ошибка запроса (encode): {e}")
    except Exception as e:
        print(f"Неожиданная ошибка (encode): {type(e).__name__} - {e}")

async def send_decode_request(client_id: str, key: str, padding: str, encoded_data: str, huffman_codes_json: str):
    url = f"{BASE_API_URL}/decode/{client_id}"
    processed_huffman_json_obj = None
    try:
        pad_int = int(padding)
        temp_huffman_str = huffman_codes_json
        if temp_huffman_str.startswith('"') and temp_huffman_str.endswith('"'):
            temp_huffman_str = temp_huffman_str[1:-1]
        elif temp_huffman_str.startswith("'") and temp_huffman_str.endswith("'"):
            temp_huffman_str = temp_huffman_str[1:-1]
        processed_huffman_json_obj = json.loads(temp_huffman_str)

    except ValueError:
        print("Ошибка: padding должен быть числом.")
        return
    except json.JSONDecodeError:
        print("Ошибка: строка Huffman кодов не является валидным JSON объектом после обработки.")
        print(f"Получено (после обработки кавычек): {temp_huffman_str}")
        return

    payload = {
        "encoded_data": encoded_data,
        "key": key,
        "huffman_codes": processed_huffman_json_obj,
        "padding": pad_int
    }
    print(f"\nОтправка запроса на декодирование: {url} с телом: {json.dumps(payload, ensure_ascii=False)}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            result = response.json()
            print(f"Ответ от сервера (decode task): {json.dumps(result, indent=2, ensure_ascii=False)}")
    except httpx.HTTPStatusError as e:
        print(f"Ошибка HTTP Status (decode): {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"Ошибка запроса (decode): {e}")
    except Exception as e:
        print(f"Неожиданная ошибка (decode): {type(e).__name__} - {e}")

async def main_loop():
    global current_client_id
    global current_websocket
    print("Консольный WebSocket клиент для сервиса шифрования.")
    print_help()

    active_client_id_for_prompt = "<disconnected>"

    while True:
        if current_websocket and current_client_id:
            active_client_id_for_prompt = current_client_id
        elif not current_websocket and current_client_id:
             active_client_id_for_prompt = f"{current_client_id} (disconnected)"
        else:
            active_client_id_for_prompt = "<disconnected>"
            current_client_id = None

        try:
            command_input = await asyncio.to_thread(input, f"client@{active_client_id_for_prompt}> ")
        except KeyboardInterrupt:
            if current_websocket:
                 print("\nДля выхода сначала выполните 'disconnect', затем 'exit', или нажмите Ctrl+D.")
            else:
                print("\nПолучен сигнал прерывания. Для выхода введите 'exit' или нажмите Ctrl+D.")
            continue
        except EOFError:
            print("\nEOF получен. Завершение работы...")
            if current_websocket:
                await disconnect_command()
            break

        if not command_input.strip():
            continue

        parts = command_input.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args_str = parts[1] if len(parts) > 1 else ""

        if cmd == "connect":
            client_id_arg = args_str.strip() if args_str.strip() else str(uuid.uuid4())
            await connect_command(client_id_arg)
        elif cmd == "disconnect":
            await disconnect_command()
        elif cmd == "encode":
            if not current_client_id or not current_websocket:
                print("Ошибка: сначала установите активное WebSocket соединение командой 'connect [client_id]'.")
                continue
            encode_args = args_str.split(maxsplit=1)
            if len(encode_args) < 2:
                print("Использование: encode <key> <text_to_encode>")
                continue
            key, text = encode_args[0], encode_args[1]
            await send_encode_request(current_client_id, key, text)
        elif cmd == "decode":
            if not current_client_id or not current_websocket:
                print("Ошибка: сначала установите активное WebSocket соединение командой 'connect [client_id]'.")
                continue
            decode_args_parts = args_str.split(maxsplit=3)
            if len(decode_args_parts) < 4:
                print("Использование: decode <key> <padding> <encoded_b64_data> \"<huffman_codes_json>\"")
                print("Совет: JSON строку с кодами Хаффмана (4-й аргумент) заключайте в двойные кавычки.")
                continue
            key, padding, encoded_b64, huffman_json_str = decode_args_parts
            await send_decode_request(current_client_id, key, padding, encoded_b64, huffman_json_str)
        elif cmd == "help":
            print_help()
        elif cmd == "exit":
            if current_websocket:
                await disconnect_command()
            print("Выход из клиента.")
            break
        else:
            print(f"Неизвестная команда: {cmd}. Введите 'help' для списка команд.")

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nПрограмма клиента принудительно завершена.")
    finally:
        print("Клиент остановлен.") 
