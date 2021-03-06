# RF-members

## Setup

Install Python 2, then install pip and virtualenv:

    $ sudo easy_install pip
    $ sudo pip install virtualenv

Next clone the repo, and set up virtualenv for this project:

    $ git clone git@github.com:realistforeningen/rf-members.git
    $ cd rf-members/
    $ virtualenv env

Whenever you want to work on this project you should run:

    $ source env/bin/activate

After that you can install dependencies using:

    $ pip install -r requirements.txt

## Database

At the moment we're using a SQLite database.  To make sure your local database
is up to date, run:

    $ python migrate.py

This doesn't do anything when your database is already up-to-date, so
it's better to run this one time too often than one time too less.

## Running app

Run the app in debug mode:

    $ ./rfmembers.sh run

Open <http://localhost:5000/>

