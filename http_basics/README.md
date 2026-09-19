# API Detective: Talk to a Public API

**Goal:** See the full cycle — `Request → API → Response → Data → Display` — before writing any FastAPI code.

**API used:** [JSONPlaceholder](https://jsonplaceholder.typicode.com) (free, no key needed)

---

---

## Why APIs exist

Humans use a shared language (like English) to understand each other. Applications need something similar — a shared way to talk to each other. That's what an **API** (Application Programming Interface) is.

A few reasons APIs exist:

**1. Almost every application needs help from something else.**
Take Notepad — its job is just to work with text. But saving or loading a `.txt` file isn't something Notepad does on its own; it uses APIs to ask the operating system to read/write the file. Even a simple app depends on APIs behind the scenes.

**2. Different applications are built in different languages.**
A Python app and a JavaScript app can't just directly read each other's code. An API defines a shared contract: *"this is how you ask me for something, and this is how I'll respond."* That contract works no matter what language either side is written in.

**3. Applications change over time — without breaking each other.**
Imagine you build an app that pulls data from someone else's API. A few months later, they update their app and change something. If there were no clear API contract, your app could break with no warning. This is why APIs are **versioned** — when something changes, a new version is published, while the old version keeps working exactly as it did before. Your app stays safe until you're ready to move to the new version.

---

## Types of APIs

REST is the type you'll be using in this activity and in the course, but it's not the only kind. A few others you'll hear mentioned:

| Type | Data format |
|---|---|
| **REST** | JSON, text, HTML |
| GraphQL | JSON |
| SOAP | XML |
| gRPC | Protocol Buffers |
| WebSockets | JSON, binary |

You don't need to learn the others right now — just recognize the names when they come up.

### HTTP methods (the actions REST APIs use)

| Method | Purpose |
|---|---|
| GET | Read/fetch data |
| POST | Create new data |
| PUT | Update existing data |
| DELETE | Remove data |

---

## Step 1 — See it in the browser first

Open this URL in your browser:

```
https://jsonplaceholder.typicode.com/todos/1
```

You'll see:

```json
{
  "userId": 1,
  "id": 1,
  "title": "delectus aut autem",
  "completed": false
}
```

This data came from an HTTP GET request — your browser asked the API for it, and the API sent back a response.

---

## Step 2 — Make the same request from Python

Make sure `requests` is installed, then create a file and run:

```python
import requests

response = requests.get("https://jsonplaceholder.typicode.com/todos/1")

print(response)
```

Expected output:

```
<Response [200]>
```

Now add:

```python
print(response.status_code)
```

Expected output:

```
200
```

`200` means the request succeeded. You haven't touched the actual data yet — just the response object.

---

## Step 3 — Turn the response into usable data

```python
print(response.text)
```

This shows the raw JSON as text.

Now convert it into a Python dictionary:

```python
data = response.json()
print(data)
```

Then pull out individual fields:

```python
print(data["title"])
print(data["id"])
print(data["userId"])
print(data["completed"])
```

Mental model: API → JSON → `response.json()` → Python dictionary.

---

## Step 4 — Practice: change the request

**Task:** Get Todo #5 instead of Todo #1.

```python
response = requests.get("https://jsonplaceholder.typicode.com/todos/5")
data = response.json()

print("Todo ID:", data["id"])
print("Title:", data["title"])
print("Completed:", data["completed"])
```

Now build a small Todo Viewer using an f-string so the ID is easy to change:

```python
import requests

todo_id = 1

response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
data = response.json()

print("TODO")
print("----------------")
print("ID:", data["id"])
print("Title:", data["title"])
print("Completed:", data["completed"])
```

Try changing `todo_id` to `10`, `50`, and `100` and rerun.

---

## Step 5 — Challenges

### Challenge A — API Detective (nested JSON)

Go to:
```
https://jsonplaceholder.typicode.com/users/1
```

Find, in the JSON, and then print with Python:
1. The user's name
2. Their username
3. Their email
4. The city they live in

Hint: the city is nested inside another field. If `address` is a dictionary inside `data`, you reach city with:

```python
data["address"]["city"]
```

### Challenge B — Todo Inspector (interactive)

Build a program that asks the user for a Todo ID and prints the result:

```python
import requests

todo_id = input("Enter a Todo ID: ")
response = requests.get(f"https://jsonplaceholder.typicode.com/todos/{todo_id}")
data = response.json()

print()
print("===== TODO INSPECTOR =====")
print("ID:", data["id"])
print("Title:", data["title"])
print("Completed:", data["completed"])
```

---

## Step 6 — Writing and filtering

Important: these writes aren't actually saved on the server — JSONPlaceholder fakes the response as if it happened. If you re-`GET` the same Todo afterward, you'll see the original data again. That's fine — the point is to see the shape of the request.

### Create a resource (POST)

```python
response = requests.post(
    "https://jsonplaceholder.typicode.com/todos",
    json={"userId": 1, "title": "learn requests", "completed": False},
)
print(response.status_code)
print(response.json())
```

Notice the response includes a new `id` (usually `201`), even though nothing was really saved on the server.

### Update a resource (PUT — full replace)

```python
response = requests.put(
    "https://jsonplaceholder.typicode.com/todos/1",
    json={"id": 1, "userId": 1, "title": "updated title", "completed": True},
)
print(response.status_code)
print(response.json())
```

### Update a resource (PATCH — partial update)

```python
response = requests.patch(
    "https://jsonplaceholder.typicode.com/todos/1", json={"completed": True}
)
print(response.status_code)
print(response.json())
```

### Delete a resource

```python
response = requests.delete("https://jsonplaceholder.typicode.com/todos/1")
print(response.status_code)
```

### Filter resources with query parameters

```python
# Only todos belonging to user 1
response = requests.get(
    "https://jsonplaceholder.typicode.com/todos", params={"userId": 1}
)
print(response.json())
```

Mental model: GET reads, POST creates, PUT/PATCH update, DELETE removes — and query parameters narrow down a GET.

---

## Step 7 — Common response codes

Every response has a status code — a number that tells you what happened, before you even look at the data. You've already seen `200`. Here are the ones you'll run into most:

| Code | Name | Meaning |
|------|------|---------|
| `200` | OK | Request succeeded (normal GET/PUT/PATCH/DELETE response) |
| `201` | Created | A new resource was successfully created (typical POST response) |
| `204` | No Content | Request succeeded, but there's nothing to send back |
| `400` | Bad Request | The request was malformed — something wrong with what *you* sent |
| `401` | Unauthorized | You need to authenticate (log in / provide credentials) |
| `403` | Forbidden | You're authenticated, but not allowed to do this |
| `404` | Not Found | The resource doesn't exist (wrong ID, wrong URL) |
| `500` | Internal Server Error | Something broke on the *server's* side, not yours |

A simple rule of thumb:
- **2xx** → success
- **4xx** → the client (you) made a mistake
- **5xx** → the server made a mistake

Try it yourself — request a Todo ID that doesn't exist and see what code comes back:

```python
response = requests.get("https://jsonplaceholder.typicode.com/todos/99999")
print(response.status_code)
```

---

## Where this is headed

Right now, your Python program is the **client** — it sends requests to someone else's API and reads the response.

```
Python program --requests.get()--> Public API
Python program <------response---- Public API
```

Next, you'll build your **own server** with FastAPI, so that other programs can send *you* requests:

```
Client --HTTP Request--> Your FastAPI app
Client <--HTTP Response-- Your FastAPI app
```

---

## Other free APIs (no key required) for extra practice

- **PokéAPI** — fun for nested JSON, searching by ID or name
- **Open-Meteo** — real weather data, good for a mini weather viewer
- **REST Countries** — nested JSON with real country data