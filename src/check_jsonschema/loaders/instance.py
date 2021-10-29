import json

import ruamel.yaml
from identify import identify

from .errors import BadFileTypeError

yaml = ruamel.yaml.YAML(typ="safe")


class InstanceLoader:
    def __init__(self, filenames, default_filetype=None):
        self._filenames = filenames
        self._default_ft = default_filetype

    @property
    def _default_loadfunc(self):
        if not self._default_ft:
            return None
        if self._default_ft.lower() == "json":
            return json.load
        return yaml.load

    def iter_files(self):
        for fn in self._filenames:
            tags = identify.tags_from_path(fn)
            if "yaml" in tags:
                loadfunc = yaml.load
            elif "json" in tags:
                loadfunc = json.load
            else:
                loadfunc = self._default_loadfunc

            # TODO: handle this by storing it in the errors map
            if not loadfunc:
                raise BadFileTypeError(
                    f"cannot check {fn} as it is neither yaml nor json"
                )

            with open(fn) as fp:
                yield (fn, loadfunc(fp))
