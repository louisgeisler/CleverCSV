#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Drop-in replacement for the Python csv writer class.

Author: Gertjan van den Burg

"""

import csv

from .dialect import SimpleDialect
from .exceptions import Error

DIALECT_KEYS = [
    "skipinitialspace",
    "doublequote",
    "strict",
    "delimiter",
    "escapechar",
    "lineterminator",
    "quotechar",
    "quoting",
]


class writer(object):
    def __init__(self, csvfile, dialect="excel", **fmtparams):
        self.original_dialect = dialect
        self.dialect = self._make_python_dialect(dialect, **fmtparams)
        self._writer = csv.writer(csvfile, dialect=self.dialect)

    def _make_python_dialect(self, dialect, **fmtparams):
        if isinstance(dialect, str):
            d = csv.get_dialect(dialect)
        elif isinstance(dialect, csv.Dialect):
            d = dialect
        elif isinstance(dialect, SimpleDialect):
            d = dialect.to_csv_dialect()
        elif dialect in [csv.excel, csv.excel_tab, csv.unix_dialect]:
            d = dialect
        else:
            raise ValueError(f"Unknown dialect type: {dialect}")

        # Override properties from format parameters
        props = {k: getattr(d, k) for k in DIALECT_KEYS if hasattr(d, k)}
        for key, value in fmtparams.items():
            props[key] = value

        # lineterminator must be set
        if "lineterminator" not in props or props["lineterminator"] is None:
            props["lineterminator"] = "\n"

        # We have to subclass the csv.Dialect
        newdialect = type("dialect", (csv.Dialect,), props)
        return newdialect

    def writerow(self, row):
        try:
            return self._writer.writerow(row)
        except csv.Error as e:
            raise Error(str(e))

    def writerows(self, rows):
        try:
            return self._writer.writerows(rows)
        except csv.Error as e:
            raise Error(str(e))
