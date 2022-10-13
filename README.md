# parseTSL
Trusted Service List parser

## Installation
- Clone this repository
- Make a virtual enviroment
- activate venv
- Install requeriments
### Debian 10 
For use of venv you need to install python3-venv package.

```
git clone https://github.com/juandn/parseTSL.git
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Use
- Empty commands run help
- Supported commands:
  - download
    - Download fixed spanish TSL.
  - list [services|providers] 
  - show
  - search [services|providers] <search string>
  - tree
  - export dir <path to dir>
  - export file <filename>
  - export keystore <filename>

