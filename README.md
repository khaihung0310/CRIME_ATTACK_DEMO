# CRIME Attack Demo Lab

A safe local simulation of the **CRIME (Compression Ratio Info-leak Made Easy)** attack using:

- Flask
- Burp Suite
- curl
- DEFLATE (`zlib`) compression

This project does **not** reproduce the original TLS-level CRIME exploit. It demonstrates the same compression oracle principle in a modern, local-only environment.

This demo was prepared for the **COMP2320 Offensive Security** presentation by **Team 244**.

---

## Overview

The original CRIME attack abused:

- TLS/SPDY request compression
- attacker-controlled input
- encrypted packet length leakage

to recover secret session cookies.

Modern browsers and TLS stacks no longer support TLS-level compression, so this demo recreates the idea locally with Python, HTTP-like request data, DEFLATE compression, and simulated TLS record overhead.

---

## Demo Architecture

```text
Attacker guess
      ↓
Internal HTTP request containing guess + hidden cookie
      ↓
DEFLATE compression using zlib
      ↓
Fake TLS record overhead is added
      ↓
Observed TLS record length
      ↓
Better guess → better compression → smaller observed length
```

The hidden cookie in the demo is:

```text
sessionid=9f86d081884c7d659a2f
```

The simulated TLS length is calculated as:

```text
observed_tls_record_length = TLS_HEADER + compressed_size + TLS_MAC + TLS_PADDING
```

where:

```text
TLS_HEADER = 5
TLS_MAC = 20
TLS_PADDING = 16
```

---

## Requirements

Check Python:

```bash
python3 --version
```

Create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install Flask:

```bash
pip install flask
```

Optional tools:

- Burp Suite Community Edition
- curl

---

## Running the Demo

Make sure the virtual environment is activated:

```bash
source venv/bin/activate
```

Start the Flask server:

```bash
python crime_demo.py
```

Expected output:

```text
Running on http://127.0.0.1:5000
```

---

## `/oracle` Attacker View

The `/oracle` endpoint is the attacker-facing view. It does not expose the internal plaintext request, the real compressed data, or the hidden cookie.

Basic format:

```bash
curl "http://127.0.0.1:5000/oracle?guess=<attacker_guess>"
```

Example:

```bash
curl "http://127.0.0.1:5000/oracle?guess=9f"
```

Example response:

```json
{
  "explanation": "Attacker view: only the simulated encrypted TLS record length is visible...",
  "guess": "9f",
  "observed_tls_record_length": 150
}
```

Try comparing guesses:

```bash
curl "http://127.0.0.1:5000/oracle?guess=9"
curl "http://127.0.0.1:5000/oracle?guess=9f"
curl "http://127.0.0.1:5000/oracle?guess=9f8"
curl "http://127.0.0.1:5000/oracle?guess=aaaa"
```

The key observation is:

```text
Correct prefix → better compression → smaller observed TLS record length
```

---

## `/debug` Teaching View

The `/debug` endpoint is for explaining the demo during a presentation. It reveals the internal HTTP-like request and the raw compressed size so students can see why the oracle works.

Example:

```bash
curl "http://127.0.0.1:5000/debug?guess=9f8"
```

The debug response includes:

- `guess`
- `fake_http_request`
- `compressed_size`
- `observed_tls_record_length`
- `match_length`

Internally, the demo builds a vulnerable-style request like this:

```http
GET /search?q=sessionid=9f8 HTTP/1.1
Host: victim.local
Cookie: sessionid=9f86d081884c7d659a2f
User-Agent: Mozilla/5.0
Accept: text/html,application/xhtml+xml
Referer: http://attacker.local/
```

The attacker-controlled query value and the hidden cookie are compressed together. If the guess repeats the cookie prefix, DEFLATE can encode the repeated text more efficiently.

---

## `/attack` Automated Recovery

The `/attack` endpoint runs a local, simplified, character-by-character recovery simulation.

Example:

```bash
curl "http://127.0.0.1:5000/attack"
```

The endpoint uses this restricted alphabet:

```text
0123456789abcdef
```

At each position, it tries one extra character, checks the simulated TLS record length, and keeps the candidate with the smallest length.

The demo also uses a few simple padding probes:

```text
"", "A", "AA", "AAA", "AAAA", "AAAAA"
```

These probes reduce ties in the compressed length signal. Real side-channel attacks often need repeated measurements, alignment, and statistical handling; this lab keeps that idea small enough to explain live.

The response includes:

- `alphabet`
- `padding_probes`
- `recovered_cookie_prefix`
- `steps`
- `explanation`

This is intentionally simple so the class can inspect the JSON and follow how compression length becomes an oracle.

---

## Burp Suite Demonstration

### 1. Start Burp Suite

Go to:

```text
Proxy -> Intercept
```

Enable:

```text
Intercept is ON
```

### 2. Use Burp Browser

Click:

```text
Open browser
```

Then visit:

```text
http://127.0.0.1:5000/oracle?guess=9f8
```

Burp should intercept the request:

```http
GET /oracle?guess=9f8 HTTP/1.1
Host: 127.0.0.1:5000
```

Click:

```text
Forward
```

The browser should display the JSON response from the Flask server.

---

## Using Repeater

For a cleaner presentation demo, use Burp Repeater.

Right-click the intercepted request and choose:

```text
Send to Repeater
```

In Repeater, change the guess manually:

```http
GET /oracle?guess=9f86 HTTP/1.1
Host: 127.0.0.1:5000
```

Click:

```text
Send
```

Then compare it with a wrong prefix:

```http
GET /oracle?guess=aaaa HTTP/1.1
Host: 127.0.0.1:5000
```

The response only shows the simulated observed TLS record length, which is closer to what a network attacker would measure.

---

## Why This Is Not a Full TLS CRIME Exploit

This demo:

- does not break encryption
- does not decrypt TLS
- does not enable TLS compression
- does not attack browsers
- does not attack real servers
- does not connect to external services
- does not reproduce the full original TLS-level CVE-2012-4929 exploit

It safely demonstrates:

- compression side-channels
- encrypted length leakage
- attacker-controlled compression oracles
- why secret cookies and attacker input should not be compressed together

The `observed_tls_record_length` value is simulated locally. It is not captured from a real TLS connection.

---

## Why Full Reproduction Is Difficult Today

A real CRIME exploit is difficult to reproduce safely today because modern browsers and servers removed the vulnerable behavior.

After CVE-2012-4929 was disclosed in 2012, major browsers disabled TLS compression. TLS 1.3 later removed TLS-level compression entirely.

Recreating the original attack would require:

- outdated browsers
- legacy OpenSSL or TLS libraries
- deprecated server configurations
- TLS/SPDY compression support

Those components are unsafe and impractical for a university presentation. This lab keeps the important security lesson while avoiding obsolete and dangerous infrastructure.

---

## Presentation Explanation

Use this explanation during the demo:

```text
This is a safe local simulation. It does not attack a real server, but it demonstrates the same DEFLATE compression oracle principle used by CRIME.

The attacker controls part of the request through the guess parameter. The hidden cookie is compressed together with the guess. When the guess matches the cookie prefix, compression becomes more efficient and the simulated TLS record length becomes smaller.

This shows how CRIME turned encrypted packet length into a side-channel oracle.
```

---

## Educational Purpose

This project is intended for:

- cybersecurity education
- university presentations
- safe local demonstrations of compression side-channels
