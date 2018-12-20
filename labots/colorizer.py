# -*- coding: utf-8 -*-
"""Applying and stripping formatting from IRC messages.

Apply style::

    colorizer.style(text, fg=None, bg=None, bold=False, italics=False, underline=False, reset=True)

Method ``style`` is used to style text with IRC attribute and / or color codes.

Examples::

    colorizer.style('Hello World!', fg=colorizer.color.green)

Strip style::

    ircmessage.unstyle(text)

Method ``unstyle`` is used to strip all formatting control codes from
IRC messages so that you can safely display and log the contents
outside of IRC in a printable format.

.. note::

    In fact, ``colorizer`` is just alias to `ircmessage`_ module,
    please refer to its documentations for more details.

.. _ircmessage: https://pypi.org/project/ircmessage/
"""

from ircmessage import *
