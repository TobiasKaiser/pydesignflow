# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

from pydesignflow import Flow
from .example_block import ExampleBlock

flow = Flow()
flow['top'] = ExampleBlock()