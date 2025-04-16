from flask import Flask, jsonify, request, Response
from flask_cors import CORS  # <-- импорт CORS
import json
import re

app = Flask(__name__)
CORS(app)  # <-- разрешаем всем доменам обращаться к эндпоинтам

ALL_ROWS = None

def parse_insert_statements(sql_path: str):
    with open(sql_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"INSERT\s+INTO\s+`libbook`\s+VALUES\s*\((.+?)\);"
    matches = re.findall(pattern, content, flags=re.DOTALL)

    all_rows = []
    for match in matches:
        row_strs = re.split(r"\)\s*,\s*\(", match)
        for row_str in row_strs:
            row_str = row_str.strip().lstrip("(").rstrip(")")
            fields = split_fields(row_str)
            all_rows.append(fields)

    return all_rows

def split_fields(row_str: str):
    fields = []
    current = []
    in_quotes = False
    quote_char = None

    for ch in row_str:
        if ch in ("'", '"'):
            if not in_quotes:
                in_quotes = True
                quote_char = ch
            elif in_quotes and ch == quote_char:
                in_quotes = False
                quote_char = None
            else:
                current.append(ch)
        elif ch == "," and not in_quotes:
            fields.append("".join(current).strip())
            current = []
        else:
            current.append(ch)

    if current:
        fields.append("".join(current).strip())

    cleaned = []
    for f in fields:
        if len(f) >= 2 and f[0] == f[-1] and f[0] in ("'", '"'):
            f = f[1:-1]
        cleaned.append(f)

    return cleaned

def rows_to_dicts(rows):
    """
    Превращает список списков в список словарей
    с ключами key1, key2, ... и значениями из rows.
    """
    result = []
    for row in rows:
        row_dict = {}
        for i, value in enumerate(row, start=1):
            row_dict[f"key{i}"] = value
        result.append(row_dict)
    return result

@app.route('/api/libbooks', methods=['GET'])
def get_libbooks():
    global ALL_ROWS
    if ALL_ROWS is None:
        ALL_ROWS = parse_insert_statements("lib.libbook.sql")

    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=50, type=int)

    if page < 1:
        page = 1
    if limit < 1:
        limit = 1

    total = len(ALL_ROWS)
    start = (page - 1) * limit
    end = start + limit
    data_slice = ALL_ROWS[start:end]

    data_page = rows_to_dicts(data_slice)

    response = {
        "page": page,
        "limit": limit,
        "total": total,
        "data": data_page
    }

    # Вместо jsonify используем Response + json.dumps(..., ensure_ascii=False).
    # Это позволит вернуть русские символы без \uXXXX.
    json_str = json.dumps(response, ensure_ascii=False)
    return Response(json_str, content_type='application/json; charset=utf-8')

if __name__ == "__main__":
    app.run(debug=True)
