#!/bin/sh
gunicorn --pythonpath shortenme app:app -b 0.0.0.0:8000