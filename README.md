
# django-deepl

`django-deepl` is a **Django app** that integrates the DeepL translation service for managing and translating `.po` files. This package allows you to automatically translate strings in `.po` files using DeepL's AI-powered translations, and it includes custom management commands for handling translations and backup versions.

## Installation

### Install with `pip`

To install the `django-deepl` package, run the following command:

```bash
pip install django-deepl
```

### Add the app to your Django project

After installation, add `django_deepl` to your `INSTALLED_APPS` in the `settings.py` file:

```python
INSTALLED_APPS = [
    ...
    'django_deepl',
    ...
]
```

## Custom Management Commands

This app provides three custom management commands that you can use to interact with `.po` translation files.

### 1. `check_translations_status`

**Description**: Check for missing translations and the completion percentage for installed Django apps.

**Usage**:

```bash
python manage.py check_translations_status
```

#### Arguments:

- No additional arguments required.

### 2. `delete_backups`

**Description**: Deletes backups. By default, it removes all backups. If the `--keep_today` option is enabled, it keeps backups made today.

**Usage**:

```bash
python manage.py delete_backups --keep_today
```

#### Arguments:

- `--keep_today`: If enabled, keeps backups created today and deletes the rest.

### 3. `translate`

**Description**: Automatically translates `msgid` strings in `.po` files into the target language, filling in the `msgstr` values.

**Usage**:

```bash
python manage.py translate
```

#### Arguments:

- `--app`: Specify which app(s) to translate (optional). If not provided, all apps will be processed.
- `--language`: Specify which language(s) `.po` file(s) to translate (optional). If not provided, all languages will be processed.
- `--overwrite`: If set, translates already translated `msgstr` values (default: `False`).
- `--split_sentences`: Controls how text should be split into sentences. Options:
  - `'1'`: Text will be split into sentences using both newlines and punctuation.
  - `'0'`: Text will not be split into sentences.
  - `'nonewlines'`: Text will be split into sentences using punctuation but not newlines.
- `--preserve_formatting`: Prevents automatic formatting correction if set to `True` (default: `True`).
- `--formality`: Controls whether translations should lean toward informal or formal language. Options:
  - `'less'`: Informal.
  - `'more'`: Formal.
- `--context`: Specifies additional context to influence translations. The characters in the context parameter are not counted toward billing.
- `--model_type`: Specifies the type of translation model to use. Options:
  - `'quality_optimized'`: Maximizes translation quality at the cost of response time.
  - `'prefer_quality_optimized'`: Default model that balances quality and response time.
  - `'latency_optimized'`: Minimizes response time at the cost of translation quality.
- `--translate_base_language`: If set, the base language `.po` file of the Django app will also be translated.
- `--no_backup`: If set, no backup files will be created for each `.po`.
- `--preferred_variant`: Specifies the preferred variant(s) for the target language (e.g., `en-us` for American English).
- `--usage`: Shows remaining usage for the DeepL API.
- `--interactive`: Enables interactive mode, which prompts for confirmation or reformulation before each translation.

---

## License

This project is licensed under the [MIT License](LICENSE).