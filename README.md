# globgroups [![PyPI - Version](https://img.shields.io/pypi/v/globgroups)](https://pypi.org/projects/globgroups)
Expands glob groups like `foo{bar,baz}` -> `["foobar", "foobaz"]`

Does not (currently) support wildcards like `*.txt`, because those are context-sensitive.

## Notes
There is a rust version of this library [globgroups.rust](https://github.com/Techcable/globgroups.rust)
