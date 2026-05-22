from flask import Flask, request, jsonify
import zlib

app = Flask(__name__)

COOKIE_NAME = "sessionid"
SECRET_VALUE = "9f86d081884c7d659a2f"

TLS_HEADER = 5
TLS_MAC = 20
TLS_PADDING = 16

ATTACK_ALPHABET = "0123456789abcdef"
ATTACK_PADDING_PROBES = ["", "A", "AA", "AAA", "AAAA", "AAAAA"]

def build_http_request(guess: str) -> str:
    return (
        f"GET /search?q={COOKIE_NAME}={guess} HTTP/1.1\r\n"
        f"Host: victim.local\r\n"
        f"Cookie: {COOKIE_NAME}={SECRET_VALUE}\r\n"
        f"User-Agent: Mozilla/5.0\r\n"
        f"Accept: text/html,application/xhtml+xml\r\n"
        f"Referer: http://attacker.local/\r\n"
        f"\r\n"
    )

def compressed_size_for_guess(guess: str) -> tuple[str, int, int]:
    fake_request = build_http_request(guess)
    request_bytes = fake_request.encode()
    compressed_size = len(zlib.compress(request_bytes))
    observed_length = TLS_HEADER + compressed_size + TLS_MAC + TLS_PADDING
    return fake_request, compressed_size, observed_length

def matching_prefix_length(guess: str) -> int:
    match_length = 0
    for guessed_char, secret_char in zip(guess, SECRET_VALUE):
        if guessed_char != secret_char:
            break
        match_length += 1
    return match_length

@app.get("/oracle")
def oracle():
    guess = request.args.get("guess", "")
    _, _, observed_length = compressed_size_for_guess(guess)

    return jsonify({
        "guess": guess,
        "observed_tls_record_length": observed_length,
        "explanation": (
            "Attacker view: only the simulated encrypted TLS record length is "
            "visible. Smaller lengths can indicate better compression when the "
            "guess matches the hidden cookie prefix."
        )
    })

@app.get("/debug")
def debug():
    guess = request.args.get("guess", "")
    fake_request, compressed_size, observed_length = compressed_size_for_guess(guess)

    return jsonify({
        "guess": guess,
        "fake_http_request": fake_request,
        "compressed_size": compressed_size,
        "observed_tls_record_length": observed_length,
        "match_length": matching_prefix_length(guess)
    })

@app.get("/attack")
def attack():
    recovered = ""
    steps = []

    for _ in range(len(SECRET_VALUE)):
        candidates = []

        for character in ATTACK_ALPHABET:
            guess = recovered + character
            probe_lengths = []

            for padding in ATTACK_PADDING_PROBES:
                probe_guess = guess + padding
                _, _, observed_length = compressed_size_for_guess(probe_guess)
                probe_lengths.append(observed_length)

            candidates.append({
                "guess": guess,
                "character": character,
                "best_observed_tls_record_length": min(probe_lengths),
                "total_observed_tls_record_length": sum(probe_lengths)
            })

        best_candidate = min(
            candidates,
            key=lambda candidate: (
                candidate["best_observed_tls_record_length"],
                candidate["total_observed_tls_record_length"]
            )
        )
        recovered = best_candidate["guess"]

        steps.append({
            "position": len(recovered),
            "selected_character": best_candidate["character"],
            "recovered_prefix": recovered,
            "best_observed_tls_record_length": best_candidate["best_observed_tls_record_length"],
            "candidates": candidates
        })

    return jsonify({
        "alphabet": ATTACK_ALPHABET,
        "padding_probes": ATTACK_PADDING_PROBES,
        "recovered_cookie_prefix": recovered,
        "steps": steps,
        "explanation": (
            "Local teaching simulation: each step tries one extra character, "
            "uses a few padding probes to reduce length ties, and keeps the "
            "candidate with the smallest simulated TLS record length. This does "
            "not connect to TLS or attack any external service."
        )
    })

if __name__ == "__main__":
    app.run(port=5000, debug=True)
