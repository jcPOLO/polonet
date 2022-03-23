[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# polonet

## Prerequisites
Install Git:
  https://git-scm.com/downloads
Install Python > 3.7:
  https://www.python.org/downloads/
Install Poetry
  https://python-poetry.org/docs/#installation

### Linux Ubuntu
In Terminal:
```
sudo add-apt-repository ppa:git-core/ppa
sudo apt update
sudo apt install git
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
git clone https://github.com/jcPOLO/polonet.git
cd polonet
poetry install
poetry shell
```

### Windows 10
Prerequisites done.
In powershell or cmd:
```
git clone https://github.com/jcPOLO/polonet.git
cd polonet
poetry install
poetry shell
```
## CLI version
```
python app.py <inventory csv file>
```
## WEB version
```
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
python app.py
````

Open http://localhost:3000

It should not be needed, but in case tasks using jinja2 templates are failing, probably you will need to manually set the NET_TEXTFSM environment variable pointing to the ntc-templates/templates directory path.
