import glob
from itertools import chain

import nbformat
from toolz import curry, compose
import logging
import sys
import json


def _read_notebook(filename):
    return nbformat.read(filename, as_version=4)


@curry
def _strip_sensitive(cell, strip_tag="stripout"):
    if "tags" in cell["metadata"].keys() and strip_tag in cell["metadata"]["tags"]:
        cell["outputs"] = []
    return cell


@curry
def _replace_strings(find_str, replace_str, cell):
    cell["source"] = cell["source"].replace(find_str, replace_str)
    return cell


def _write_notebook(notebook_filename, nb):
    nbformat.write(nb, notebook_filename)


def _setup_logger(debug=False):
    logger = logging.getLogger(__name__)
    level = logging.DEBUG if debug else logging.ERROR
    logger.setLevel(level)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(sh)


def _expand_path(notebook_path):
    return glob.glob(notebook_path)


class NBToolz(object):
    def __init__(self, *notebooks, debug=False):
        super().__init__()
        _setup_logger(debug=debug)
        self._logger = logging.getLogger(__name__)

        self._notebooks = list(chain(*map(_expand_path, notebooks)))
        self._functions_list = []

    def strip_output(self, strip_tag="stripout"):
        """Strip the output of tagged cells
        
        Args:
            strip_tag: Tag to search for

        Returns:
            NBToolz
        """
        self._logger.debug(f"Adding function: Strip out tag {strip_tag}")
        self._functions_list.append(_strip_sensitive(strip_tag=strip_tag))
        return self

    def replace(self, find_str, replace_str):
        """Replace strings in the notebook cells
        
        Args:
            find_str: String to search for
            replace_str: String to replace with

        Returns: 
            NBToolz

        """
        self._logger.debug(f"Adding function: Replace {find_str} with {replace_str}")
        self._functions_list.append(_replace_strings(find_str, replace_str))
        return self

    def _execute(self):
        self._logger.info("Executing...")
        functions = compose(*reversed(self._functions_list))
        for nb_filename in self._notebooks:
            self._logger.info(f"Reading from {nb_filename}")
            nb = _read_notebook(nb_filename)
            nb.cells = list(map(functions, nb.cells))
            yield nb

    def print(self):
        """Print output of transformation
        
        Returns: 
            None

        """
        for nb in self._execute():
            print(json.dumps(nb, indent=4))

    def write(self, *output):
        """Write output to notebook file
        
        Args:
            output: One or more files to write the output to

        Returns: 
            None
        """
        for nb, out in zip(self._execute(), output):
            self._logger.info(f"Writing to {out}")
            _write_notebook(out, nb)

    def overwrite(self):
        """Overwrite the input notebook
        
        Returns: 
            None

        """
        self.write(*self._notebooks)


if __name__ == "__main__":
    import fire

    fire.Fire(NBToolz)
