# CRIME Attack Demo Lab

A safe local simulation of the **CRIME (Compression Ratio Info-leak Made Easy)** attack using:

- Flask
- Burp Suite
- curl
- DEFLATE (`zlib`) compression

This project does **not** reproduce the original TLS-level CRIME exploit. Instead, it demonstrates the same **compression oracle principle** behind the vulnerability in a modern and safe local environment.

This demo was prepared for the **COMP2320 Offensive Security** presentation by **Team 244**.

---

## Overview

The original CRIME attack abused:

- TLS/SPDY compression
- attacker-controlled input
- encrypted packet length leakage

to recover secret session cookies.

Modern browsers and TLS 1.3 no longer support TLS-level compression, so this demo recreates the same idea locally using Python, HTTP traffic, and DEFLATE compression.

---

## Demo Architecture

```text
Attacker input
      ↓
HTTP request + secret cookie
      ↓
DEFLATE compression using zlib
      ↓
Compressed size oracle
      ↓
More accurate guess → smaller compressed size
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

Install Flask inside the virtual environment:

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

## Testing with curl

Basic format:

```bash
curl "http://127.0.0.1:5000/oracle?guess=<attacker_guess>"
```

Example guesses:

```bash
curl "http://127.0.0.1:5000/oracle?guess=S"
curl "http://127.0.0.1:5000/oracle?guess=SE"
curl "http://127.0.0.1:5000/oracle?guess=SEC"
curl "http://127.0.0.1:5000/oracle?guess=SECR"
curl "http://127.0.0.1:5000/oracle?guess=SECD"
```

---

## Expected Behaviour

More accurate guesses usually produce:

- better compression
- smaller compressed size

Example pattern:

```text
Guess: S      → smaller than a random guess
Guess: SE     → smaller again
Guess: SEC    → smaller again
Guess: SECR   → better than SECD if the secret starts with SECR
Guess: SECD   → partial match, but worse than the correct next character
```

This demonstrates the compression side-channel used by CRIME: matching input creates repeated strings, repeated strings compress better, and smaller compressed output reveals information about the secret.

---

## What HTTP Looks Like Internally

A real request to the local Flask oracle looks like this:

```http
GET /oracle?guess=SE HTTP/1.1
Host: 127.0.0.1:5000
```

Inside the demo, the server builds a vulnerable-style HTTP request like this:

```http
GET /search?q=session=SE HTTP/1.1
Host: victim.local
Cookie: session=SECRET
```

Where:

```text
q=session=SE             attacker-controlled guess
Cookie: session=SECRET   hidden secret cookie
```

If the guess matches part of the secret cookie, the repeated text compresses more efficiently.

---

## Burp Suite Demonstration

### 1. Start Burp Suite

Go to:

```text
Proxy → Intercept
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
http://127.0.0.1:5000/oracle?guess=SE
```

Burp should intercept the request:

```http
GET /oracle?guess=SE HTTP/1.1
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
GET /oracle?guess=SECR HTTP/1.1
Host: 127.0.0.1:5000
```

Click:

```text
Send
```

The response will appear inside Burp Suite:

```json
{
  "guess": "SECR",
  "compressed_size": 84
}
```

Try comparing:

```text
S
SE
SEC
SECR
SECD
SECRET
```

The key observation is:

```text
Correct prefix → better compression → smaller compressed size
```

---

## Important Notes

This demo:

- does not break encryption
- does not decrypt TLS
- does not attack real servers
- does not reproduce the full original TLS-level CRIME exploit

It safely demonstrates:

- compression side-channels
- packet length leakage
- attacker-controlled compression oracles

---

## Why a Real CRIME Exploit Is Difficult Today

A full real-world CRIME exploit is difficult to reproduce today because modern browsers and servers no longer support TLS compression.

After CVE-2012-4929 was disclosed in 2012, major browsers such as Chrome and Firefox disabled TLS compression. TLS 1.3 later removed TLS-level compression entirely.

Recreating the original CRIME attack would require:

- outdated browsers
- legacy OpenSSL/TLS implementations
- deprecated server configurations

These are no longer practical or secure to deploy for a class presentation.

---

## Presentation Explanation

Use this explanation during the demo:

```text
This is a safe local simulation. It does not attack a real server, but it demonstrates the same DEFLATE compression oracle principle used by CRIME.

The attacker controls part of the request through the guess parameter. The hidden cookie is compressed together with the guess. When the guess matches the cookie prefix, compression becomes more efficient and the compressed size becomes smaller.

This shows how CRIME turned encrypted packet length into a side-channel oracle.
```

---

## Educational Purpose

This project is intended for:

- cybersecurity education
- university presentations
- side-channel attack demonstrations
- protocol security research

Only use this project in safe and authorised environments.
