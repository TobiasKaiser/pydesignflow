# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from importlib.metadata import version, PackageNotFoundError

try:
    version = version("pydesignflow")
except PackageNotFoundError:
    version = "unknown"
