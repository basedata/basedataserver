# basedata.org server

install mongodb server and python bindings:

    apt-get install mongodb-server python-pymongo

get code and setup server:

    cd /srv/
    git clone https://github.com/basedata/basedataserver
    cd basedataserver
    virtualenv --system-site-packages .
    pip -E . install -r requirements.txt
    ./manage.py syncdb
    ./manage.py runserver
