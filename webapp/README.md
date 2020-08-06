# FLOnt: Web Application

This web application implements a client view for interacting with the populated
ontology. It runs under the [Django](https://www.djangoproject.com/) framework.

## Getting Started

### Prerequisites

You'll need Python 3.6+.

### Installation

1. Install the module from its custom package repository.
    ```bash
    pip install --extra-index-url="https://packages.chalier.fr" django-flont
    ```

2. Add `flont` to your Django project `INSTALLED_APPS`

3. Migrate the database:
    ```bash
    python manage.my migrate
    ```

4. Collect the new static files (override if necessary):
    ```bash
    python manage.my collectstatic
    ```

5. Integrate `flont.urls` in your project URLs

## Demonstration

![Webapp Demo](https://i.imgur.com/SQwJ6yD.png)
