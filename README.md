# nitrogfx-py

nitrogfx-py is a Python library for handling Nintendo DS graphics formats. It can deserialize and serialize the formats and do some basic conversions with them.

Currently it supports:

- NCGR/NCBR tilesets
- NSCR tilemaps
- NCLR palettes
- NCER sprite data

The formats aren't perfectly implemented so the this most likely won't work with every game out there.

## Install from pip

    pip install nitrogfx-py

## Install from source (for development)

    git clone https://gitlab.com/Fexean/ntrgfx-py
    pip install --upgrade pip
    pip install -e ntrgfx-py

## Documentation

The code is documented with docstrings. You can view them online at: https://fexean.gitlab.io/ntrgfx-py/nitrogfx.html

