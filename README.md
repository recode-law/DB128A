# DB128A

A Django project that powers two related public feedback platforms for German courts on a shared codebase:

- **video_conference** ([videoverhandlung.de](https://videoverhandlung.de)) — a directory of courts with feedback on video hearings.
- **ai_usage** ([KI-vor-Gericht.de](https://ki-vor-gericht.de)) — a directory of courts with feedback on the use of AI in court proceedings.

Both modes share the `court_database`, `user_signup`, and `helper` apps (court data, verified-user signup, and common utilities).

## Requirements

- Python 3.10 (specifically 3.10, because some library code does not work on newer python functions. Maybe this will be adressed in the future.)
- The Python packages listed in [requirements.txt](requirements.txt):

  ```bash
  pip install -r requirements.txt
  ```

- A MySQL client library for production use (e.g. `mysqlclient`), since [DB128A/settings/production.py](DB128A/settings/production.py) uses `django.db.backends.mysql`. It isn't pinned in `requirements.txt` because it needs matching system MySQL headers, so install it separately for your platform.
- A `gpg` binary on the `PATH` if you want encrypted database backups (`django-dbbackup` + `python-gnupg`, configured via `VVDE_GPG_RECIPIENT`).
- A `.env` file in the project root (loaded via `python-dotenv`, see [DB128A/settings/base.py](DB128A/settings/base.py)) providing at least:
  - Database credentials (`VVDE_DB_NAME`, `VVDE_DB_USERNAME`, `VVDE_DB_PASSWORD`, `VVDE_DB_HOSTNAME`, `VVDE_DB_PORT`)
  - Allowed hostnames (`VVDE_HOSTNAME`)
  - Email/SMTP settings (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`)
  - Signup captcha keys (`VVDE_USER_SIGNUP_CAPTCHA_PUBLIC_KEY`, `VVDE_USER_SIGNUP_CAPTCHA_SECRET_KEY`)
  - S3 backup storage (`VVDE_S3_ACCESS_KEY`, `VVDE_S3_SECRET_KEY`, `VVDE_S3_BUCKET_NAME`, `VVDE_GPG_RECIPIENT`)
  - Admin contact (`VVDE_ADMIN_NAME`, `VVDE_ADMIN_EMAIL`)

## Deployment

This is a standard Django 5.0 project, so the official [Django deployment documentation](https://docs.djangoproject.com/en/5.0/howto/deployment/) and its [deployment checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/) apply directly — use them for WSGI server setup (e.g. gunicorn/uWSGI), static file serving, HTTPS, and other production hardening.

A few project-specific notes:

- Production uses `DB128A.settings.production` as the settings module (set via `DJANGO_SETTINGS_MODULE`), which requires `DEBUG=False` and reads all secrets from the environment/`.env` — see the Requirements section above.
- `SECRET_KEY` is read from `DB128A/settings/django_secret_key.txt` and generated automatically on first run if that file doesn't exist yet.
- Run `python manage.py collectstatic` before serving in production, since `STATIC_ROOT` is set to `staticfiles/`.
- Which application (`video_conference` or `ai_usage`) is served depends on the `DB128A_CONTEXT` environment variable — see the next section.

## Switching between application modes

This project bundles two separate applications, `video_conference` and `ai_usage`, that are otherwise identical at the infrastructure level. Which one is active is controlled entirely by the `DB128A_CONTEXT` environment variable, which selects the URL configuration (`ROOT_URLCONF`) and WSGI module (`WSGI_APPLICATION`) — see [DB128A/settings/base.py](DB128A/settings/base.py).

**In production**, each mode has its own WSGI entry point that sets `DB128A_CONTEXT` for you:

- [DB128A/wsgi_video_conference.py](DB128A/wsgi_video_conference.py) — serves the `video_conference` app
- [DB128A/wsgi_ai_usage.py](DB128A/wsgi_ai_usage.py) — serves the `ai_usage` app

Point your WSGI server (gunicorn, uWSGI, mod_wsgi, ...) at whichever module matches the mode you want to run. Because the context is chosen once per process, running both modes at the same time requires two separate deployments (e.g. two gunicorn processes behind two vhosts/domains), each pointed at its own WSGI module.

**For local development** with `manage.py`, set `DB128A_CONTEXT` explicitly before running a command, since `manage.py` only defaults `DJANGO_SETTINGS_MODULE` to `DB128A.settings.dev` and does not set a context on its own:

```bash
DB128A_CONTEXT=video_conference python manage.py runserver
# or
DB128A_CONTEXT=ai_usage python manage.py runserver
```

## License

Licensed under the GNU Affero General Public License v3.0 — see [LICENSE](LICENSE).
