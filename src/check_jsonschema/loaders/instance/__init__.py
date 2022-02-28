import json
import typing as t

import ruamel.yaml
from identify import identify

from ...transforms import TransformT
from ..errors import BadFileTypeError
from . import json5

yaml = ruamel.yaml.YAML(typ="safe")


LOAD_FUNC_BY_TAG: t.Dict[str, t.Callable] = {
    "json": json.load,
    "yaml": yaml.load,
}
if json5.ENABLED:
    LOAD_FUNC_BY_TAG["json5"] = json5.load
MISSING_SUPPORT_MESSAGES: t.Dict[str, str] = {
    "json5": json5.MISSING_SUPPORT_MESSAGE,
}


class InstanceLoader:
    def __init__(
        self,
        filenames,
        default_filetype: t.Optional[str] = None,
        data_transform: t.Optional[TransformT] = None,
    ):
        self._filenames = filenames
        self._default_ft = default_filetype.lower() if default_filetype else None
        self._data_transform = data_transform

    def get_loadfunc(self, filename):
        tags = identify.tags_from_path(filename)
        for (tag, loadfunc) in LOAD_FUNC_BY_TAG.items():
            if tag in tags:
                return loadfunc
        if self._default_ft in LOAD_FUNC_BY_TAG:
            return LOAD_FUNC_BY_TAG[self._default_ft]

        for tag in tags:
            if tag in MISSING_SUPPORT_MESSAGES:
                raise BadFileTypeError(
                    f"cannot check {filename} because support is missing for {tag}\n"
                    + MISSING_SUPPORT_MESSAGES[tag]
                )
        raise BadFileTypeError(
            f"cannot check {filename} as it is not one of the supported filetypes: "
            + ",".join(LOAD_FUNC_BY_TAG.keys())
        )

    def iter_files(self):
        for fn in self._filenames:
            loadfunc = self.get_loadfunc(fn)

            with open(fn) as fp:
                data = loadfunc(fp)
                if self._data_transform:
                    data = self._data_transform(data)
                yield (fn, data)


def instance_loader_from_args(args):
    return InstanceLoader(
        args.instancefiles,
        default_filetype=args.default_filetype,
        data_transform=args.data_transform,
    )
