from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="django-deepl",
    version="0.0.5",
    description="Django app to translate .po files using DeepL translation service",
    author="iTz-i-Soldier",
    author_email="iTz-i-Soldier@users.noreply.github.com",
    url="https://github.com/iTz-i-Soldier/django-deepl",  
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=3.0',
        'polib==1.2.0',
        'deepl==1.21.0',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
