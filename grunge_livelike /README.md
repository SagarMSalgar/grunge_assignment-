# Grunge Rock Development Application

## Overview

This Django project implements a catalogue of Grunge rock music.  It has a fully-functional Django admin interface, and a read-only REST API.  It contains three related data models:

1. `Artist`
2. `Album`
3. `Track`

If you are applying for a Full Stack role, your submission should satisfy the Full Stack Candidate goals.
Otherwise, your submission should satisfy the Backend Candidate goals.

## Backend Candidate Goals

* Implement the ability to fetch, create, update, and delete playlists through the REST API.  A playlist should have a `uuid`, a `name`, and contain 0 or more tracks from this catalogue.  The tracks should be orderable in the playlist.
* Implement the test cases in `tests/test_playlists.py`.  The goal is to have no skipped or failing tests.
* Update the Django admin with the ability to browse and manage playlists.

## Fullstack Candidate Goals

* Implement the ability to fetch, create, update, and delete playlists using Django views and templates.  A playlist should have a `uuid`, a `name`, and contain 0 or more tracks from this catalogue.  The tracks should be orderable in the playlist.
* Update the Django admin with the ability to browse and manage playlists.


## Django Code Assessment Criteria

Used for Backend and Fullstack role code assessments.  All submissions will be evaluated based on these base criteria, and specific roles might have some additional points to consider.

* Ability to run the project. Reviewers should be able to run the project locally using standard processes like `manage.py` or Foreman.
* Tidiness of the source code repository. No stray files like logs, virtual environments, databases, etc.
* Adherence to Python code style established by the community standards like PEP-8.
* Conformance to the Django Architecture. Proper use of models, views, templates, and preferring features and utilities provided by Django rather than candidate rolling their own.
* Command of Django. Show off how deep your knowledge of Django and its ecosystem is and how much you can defer to the framework to achieve a good power-to-weight ratio.
* Query efficiency. Avoid problems like N+1 queries or duplicated queries.
* Cohesiveness of the project. No missing files, broken styles, stub features, etc.
* Submission process adherence. Submission should be a pull request. Commits should be atomic with clear messages.

### Backend Engineer Focus

* Admin experience of managing albums. We will be looking at how effectively someone would be able to manage albums, tracks, and playlists through the admin. Admin users will want to update details, re-order tracks, and so on.
* Strength of the data model. It is important for data to be modeled in a way that supports robust APIs and useful admin views, and also enforces domain rules.

## Developing

You can check your work at any time by running:

```shell
$ make ready
```

This will run the default code linters and the test suite.  You can format your code to what the linters expect with:

```shell
$ make format
```

Please ensure that there are no code format or lint errors.

## Getting started

#### Create an account

Create an account at [https://code.livelike.com/user/sign_up](https://code.livelike.com/user/sign_up)

#### Fork this repository

When you have completed the goals then you can open a Pull Request to this main repository.

### Set up a virtualenv

This application is compatible with Python 3.10 and later.  You can set up a virtual environment with:

```shell
$ python3 -m venv --upgrade-deps venv
$ source venv/bin/activate
```

### Install dependencies

```shell
$ python3 -m pip install --requirement=requirements.txt
```

### Initialize the development database

```shell
$ python3 manage.py migrate
$ python3 manage.py loaddata initial_data
```

### Add a development superuser

```shell
$ python3 manage.py createsuperuser
```

### Run the development server

```shell
$ python3 manage.py runserver
```

Log into the Django admin with your superuser account at:

[http://localhost:8000/admin/](http://localhost:8000/admin/)

Browse the REST API at:

[http://localhost:8000/api/v1/](http://localhost:8000/api/v1/).
