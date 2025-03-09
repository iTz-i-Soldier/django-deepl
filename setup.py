from setuptools import setup, find_packages

setup(
    name="django-deepl",
    version="0.1.1",
    description="Django app to translate .po files using DeepL translation service",
    author="iTz-i-Soldier",
    author_email="no",
    url="https://github.com/iTz-i-Soldier/django-deepl",  
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
