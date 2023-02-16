[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# polonet

## Prerequisites
- Install Git:  
https://git-scm.com/downloads
- Install Python > 3.7:  
https://www.python.org/downloads/
- Install Poetry  
https://python-poetry.org/docs/#installation

### Linux Ubuntu
In Terminal:
```
sudo add-apt-repository ppa:git-core/ppa
sudo apt update
sudo apt install git
curl -sSL https://install.python-poetry.org | python3 -
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

### Docker
```
git clone https://github.com/jcPOLO/polonet.git
cd polonet
docker build -t polonet .
docker run -d --name polonet -p 5000:5000 polonet

## CSV format
```
hostname,platform,port,site,whatever
1.1.1.1,ios,22,Zaragoza,Anchoas
2.2.2.2,fortinet,22,Huesca,Boquerones
3.3.3.3,huawei,22,Teruel,Sardinas
4.4.4.4,ios_telnet,23,Pamplona,Chorizo
```
Only hostname column is mandatory.

Default values:
- platform = ios
- port = 22

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

Open http://127.0.0.1:5000/

It should not be needed, but in case tasks using jinja2 templates are failing, probably you will need to manually set the NET_TEXTFSM environment variable pointing to the ntc-templates/templates directory path.
