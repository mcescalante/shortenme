# URL Shortener

This is a URL shortener written in Flask with a user interface styled with tailwindcss and SQLite for storing data.

# Running

The easiest way to run this application is as a container via the Dockerfile. 

Assuming you would like to run this on `localhost:8000` (default), build and run:
```
docker build -t shortenme .
docker run -p 8000:8000 --name shortenme shortenme
```

Visit http://localhost:8000 to see the application's user interface, or just begin using [the API](#api-endpoints).

If you would like to deploy

Alternatively, you can follow the development setup below and run the applicaton without a container.

# Deployment

## Container

The simplest way to deploy this application is as a container. Use the included Dockerfile which uses gunicorn and is ready for production. 

1. build the container and specify your deploy URL with `docker build -t shortenme --build-arg DEPLOY_URL=http://example.com/ .`
    - If you would like to run the application on a port other than 8000, edit the port in `gunicorn.sh`
2. push it to Docker Hub or your chosen container registry
3. run the container from a docker ready platform or a VM

## Non-Container

If you wish to deploy this application directly without using a container it is still recommended to use gunicorn which is a production ready WSGI HTTP server. You should follow the development setup below on the system you wish to deploy to. To start the application, use the script `gunicorn.sh` or utilize the `gunicorn` command in the file with an init daemon such as systemd. 

Although it is not necessary, it is still recommended that you use a web server such as nginx, apache, or caddy as they offer numerous benefits.


# Development

## Setup

Create a virtualenv (optional) and install the requirements

```bash
virtualenv venv -p python3
source venv/bin/activate
pip install -r requirements.txt
```

Create the necessary database schema in the app folder `shortenme`

```bash
FLASK_APP=shortenme/app.py python -m flask init-db

#Alternatively, you can do this directly without flask cli
sqlite3 shortenme/app.db < shortenme/schema.sql
```

This project uses tailwindcss for styling the frontend. Additional CSS styles should be added to `main.css`. Tailwind is a utility first framework, and classes are used in html for styling. **Do not** edit `style.css` directly as it is a built file. 

If you wish to edit styles you must install tailwindcss with `npm`. You can then watch the html & css files for changes which writes only the necessary styles to a minified static CSS file (`style.css`) to keep it as small as possible.

```bash
npm install
npx tailwindcss -i shortenme/static/main.css -o shortenme/static/style.css --watch --minify
```

Now, you can run the project's development server

```
python shortenme/app.py
```

Visit http://localhost:5000 to see the user interface or begin using [the API](#api-endpoints).

## Running Tests

After your local dev environment is set up, you can execute tests for the application (`tests/app_test.py`) by navigating to the tests folder and running pytest:

```bash
cd tests
python -m pytest -rA

# or if you are in the root directory
python -m pytest tests -rA
```

# API Endpoints

- `POST /api/create`
  - `url` is the only required payload item
  - A random short URL will be generated if none is provided

  Payload:
  ```json
  {
    "url": "example.com",
    "shorturl": "my-short-url",
    "expiry": "2022-02-16T23:35:00"
  }
  ```

  Response:
  ```json
  {
    "result": "success",
    "short_url": "my-short-url",
    "url": "http://localhost:5000/my-short-url"
  }
  ```

- `DELETE /api/delete`

  Payload (required):
  ```json
  {
    "shorturl": "short"
  }
  ```

  Response:
  ```json
  {
    "deleted": "success"
  }
  ```

- `GET /api/analytics/<short_url>`

  Response:
  ```json
  {
    "created_utc": "2022-02-16 18:44:02",
    "expiry": "2022-02-16T23:35:00",
    "source_url": "http://example.com",
    "views": 0
  }
  ```