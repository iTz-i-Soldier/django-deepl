
# django-deepl

`django-deepl` is a **Django app** that integrates the DeepL translation service for managing and translating `.po` files. This package allows you to automatically translate strings in `.po` files using DeepL's AI-powered translations, and it includes custom management commands for handling translations and creating backup versions.

## Installation

To install the `django-deepl` package, run the following command:

```bash
pip install django-deepl
```

## Configuration in `settings.py`

### Add the app to your Django project

After installing, include `django_deepl` in the `INSTALLED_APPS` list in your `settings.py` file:

```python
INSTALLED_APPS = [
    ...
    'django_deepl',
    ...
]
```

### 1. `DEEPL_API_KEY`

You need to add your **DeepL API key** to your `settings.py` file:

```python
DEEPL_API_KEY = 'your_deepl_api_key_here'
```

Obtain your API key by signing up for a DeepL account at [DeepL](https://www.deepl.com/signup).

***Once the API key is set, you can start using and testing the app immediately. If you'd like to customize other settings, you can find them here below.***

### 2. `TRANSLATION_IGNORE_PATTERNS`

This setting defines a list of regular expressions that identify variables or placeholders which should **not** be translated, such as `{name}` or similar patterns in your translation strings. By default, common patterns are included, but you can customize it as needed:

```python
TRANSLATION_IGNORE_PATTERNS = 
    [
        r'%\(\w+\)',  # For % placeholders like %(name)s
        r'%\(\w+\)[sd]',  # For % placeholders with types like %(name)s or %(count)d
        r'%[dsf]',  # For standalone % characters
        r'(\{\{[^{}]+\}\}|\{[^{}]+\})',  # For placeholders in curly braces like {{name}} or {count}
    ]
```

This ensures that certain variables or dynamic content in your translation files are excluded from translation.

### 4. `IGNORE_TAGS_TEXT`

This setting defines the text to be used inside ignored tags. By default, it is set to `ddlit`:

```python
IGNORE_TAGS_TEXT = 'ddlit'
```

### 5. `IGNORE_TAGS`

This setting specifies the start and end tags that wrap content **not** to be translated, as long as it matches the patterns defined in the `TRANSLATION_IGNORE_PATTERNS` list:

```python
IGNORE_TAGS = (f'<{IGNORE_TAGS_TEXT}>', f'</{IGNORE_TAGS_TEXT}>')
```

### 6. `BACKUP_FILE_NAME`

This setting defines the name of the backup file created before any translation changes are applied. By default, it is set to `django_deepl_backup`:

```python
BACKUP_FILE_NAME = 'django_deepl_backup'
```

### 7. `PO_FILE_EXTENSION`

This setting specifies the file extension for translation files. By default, it is set to `.po`:

```python
PO_FILE_EXTENSION = ".po"
```

### 8. `PO_FILE_NAME`

This setting defines the default `.po` file name in Django. By default, it is set to `django`:

```python
PO_FILE_NAME = 'django'
```

## Custom Management Commands

This app provides three custom management commands that allow you to interact with `.po` translation files.

### 1. `check_translations_status`

**Description**: Check for missing translations and see the translation completion percentage for all Django apps.

**Usage**:

```bash
python manage.py check_translations_status
```

#### Arguments:
- `--app`: Specify which app(s) (optional). If not provided, all apps will be processed.
- `--language`: Specify which language(s) (optional). If not provided, all languages will be processed.

### 2. `delete_backups`

**Description**: Deletes backup files. By default, it removes all backups. If the `--keep_today` option is used, it will retain backups made today.

**Usage**:

```bash
python manage.py delete_backups
```

#### Arguments:
- `--keep_today`: Retains backups made today and deletes the rest.

### 3. `translate`

**Description**: Automatically translates `msgid` strings in `.po` files into the target language, filling in the `msgstr` values.

**Usage**:

```bash
python manage.py translate
```

#### Arguments:
- `--app`: Specify which app(s) to translate (optional). If not provided, all apps will be processed.
- `--language`: Specify which language(s) `.po` file(s) to translate (optional). If not provided, all languages will be processed.
- `--overwrite`: If set, will translate already translated `msgstr` values.
- `--split_sentences`: Controls how text is split into sentences. Options:
  - `'1'`: Splits text into sentences using both newlines and punctuation.
  - `'0'`: Does not split text into sentences.
  - `'nonewlines'`: Splits text into sentences using punctuation, but not newlines (default).
- `--preserve_formatting`: Prevents automatic formatting corrections if set to `True` (default: `True`).
- `--formality`: Controls whether translations should be informal or formal. Options:
  - `'less'`: Informal (default).
  - `'more'`: Formal.
- `--context`: Specifies additional context to influence translations. The characters in the context parameter are not counted toward billing.
- `--model_type`: Specifies the type of translation model to use. Options:
  - `'quality_optimized'`: Maximizes translation quality at the cost of response time.
  - `'prefer_quality_optimized'`: Default model that balances quality and response time.
  - `'latency_optimized'`: Minimizes response time at the cost of translation quality.
- `--translate_base_language`: If set, translates the base language `.po` file of the Django app as well.
- `--no_backup`: If set, no backup files will be created for each `.po`.
- `--preferred_variant`: Specifies the preferred variant(s) for the target language (e.g., `en-us` for American English).
- `--usage`: Displays the remaining usage for the DeepL API.
- `--interactive`: Enables interactive mode, prompting for confirmation or reformulation before each translation.

---
