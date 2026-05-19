from flask import Flask, request, jsonify
import zlib

app = Flask(__name__)

SECRET = "SECRET"
PREFIX = "session="

def build_http_request(guess: str) -> str:
    return (
        f"GET /search?q={PREFIX}{guess} HTTP/1.1\r\n"
        f"Host: victim.local\r\n"
        f"Cookie: {PREFIX}{SECRET}\r\n"
        f"\r\n"
    )

@app.get("/oracle")
def oracle():
    guess = request.args.get("guess", "")
    fake_request = build_http_request(guess)
    compressed = zlib.compress(fake_request.encode())

    return jsonify({
        "guess": guess,
        "compressed_size": len(compressed),
        "fake_http_request": fake_request
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)