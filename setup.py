from distutils.core import setup
import py2exe
setup(
    console = [{
        'script': 'main.py',
        'copyright': 'Copyright (C) 2021 LOLED Virtual',
        'company_name': 'LOLED Virtual',
        "dest_base" : "SerialEncoder",
    }],
    version = '1.0.0.0',
    name = 'SerialEncoder',
    description = 'Converts Glassmark encoder serial data to LONET',
)