# nitrogfx-py

nitrogfx-py is a Python library for handling Nintendo DS graphics formats. It can deserialize and serialize the formats and do some basic conversions with them.

Currently it supports:

- NCGR/NCBR tilesets
- NSCR tilemaps
- NCLR palettes
- NCER sprite data
- NANR animation data

The formats aren't perfectly implemented so this most likely won't work with every file from every game out there.

## Install from pip

    pip install nitrogfx-py

## Install from source (for development)

    git clone https://gitlab.com/Fexean/ntrgfx-py
    pip install --upgrade pip
    pip install -e ntrgfx-py

## Documentation

The code is documented with docstrings.

You can view them online at: https://fexean.gitlab.io/ntrgfx-py

## Dependencies

The project requires Pillow 7.0.0. You also need to have a C compiler installed on your system to be able to compile the project's C extensions.

It also has an optional dependency on orjson. If installed, the json conversion functions will run much faster.
