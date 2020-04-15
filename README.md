## Overview

![alt text](http://i.imgur.com/y5Zv9Az.png "Revealing the correct card")

## Installation

pip install -r requirements.txt

## Configuring the Server

Edit ``config.json`` to specify which port to run on,
and to point to the location of each card deck
(see ``static/cards/README.txt``).

## Starting the Server

python server.py

## Using Docker

To build the Docker image run:

```
docker build -t dixit .
```

which creates a Docker image named `dixit`.

You can then run the image using

```
docker run -p 8888:8888 -v <cards_folder>:/app/static/cards/dixit dixit
```

(replace `cards_folder` with the absolute path to a folder containing your cards).
