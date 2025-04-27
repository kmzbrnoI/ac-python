AC client library for Python
============================

This repository contains Python 3 package `ac`, which is a library for using
[hJOPserver's](https://github.com/kmzbrnoI/hJOPserver) [AC
API](https://github.com/kmzbrnoI/hJOPserver/wiki/panelServer-ac) nicely.

See `test/basic.py` or `examples` for examples of using.

## Howto create your own AC client

* If you just want to execute predefined steps, look at `examples/dance.py`
  and simply modify the file.
* If you want to implement general AC client, inherit your own class from 'AC'
  class. Look at `examples/autojc.py`.

## Project structure

 * `ac`: main ac library
   - `ac.py`: AC class definition. You should subclass this class to create
     your own specific AC.
   - `blocks.py`: interface for Panel Server *BLOCKS API*: registering
      blocks for change events, processing change events.
   - `events.py`: decorators for global events (`on_connect`, `on_disconnect`,
      ...)
   - `panel_client.pt`, `pt.py`: Panel Server & PT server connection managers.
 * `utils`: higher-level abstract utils used mainly in `examples`, but can
   contain also other utils. Utils are indended for importing in other projects.
 * `examples`: examples of using `ac` library, not intended to import from
   other projects.
   - Use `examples/template.py` for creating your own AC.
 * `test`: tests of AC library.

## Authors

This project was created by:

 * Jan Horacek ([jan.horacek@kmz-brno.cz](mailto:jan.horacek@kmz-brno.cz))

## Licence

This project in available under
[Apache License v2.0](https://www.apache.org/licenses/LICENSE-2.0).
