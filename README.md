# URL Shortener

This is a URL shortener written in Flask with a user interface styled with tailwindcss.

# Development

## Setup

Create a virtualenv (optional) and install the requirements

```bash
virtualenv venv -p python3
source venv/bin/activate
pip install -r requirements.txt
```

Create the necessary database schema with SQLite

```bash
sqlite3 app.db < schema.sql
```

This project uses tailwindcss for styling. If you are going to be editing CSS in `style.css` or style classes in the html templates, you must install tailwindcss with `npm`. You can then watch the html & css files for changes which writes only the necessary styles to a static CSS file

```bash
npm install
npx tailwindcss -i ./static/main.css -o static/style.css --watch
```

Now, you can run the project's development server

```
python app.py
```

Visit http://localhost:5000 to see the user interface