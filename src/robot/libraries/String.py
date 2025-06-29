#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
import re
from fnmatch import fnmatchcase
from random import randint
from string import ascii_lowercase, ascii_uppercase, digits

from robot.api import logger
from robot.api.deco import keyword
from robot.utils import FileReader, parse_re_flags, plural_or_not as s, type_name
from robot.version import get_version


class String:
    """A library for string manipulation and verification.

    ``String`` is Robot Framework's standard library for manipulating
    strings (e.g. `Replace String Using Regexp`, `Split To Lines`) and
    verifying their contents (e.g. `Should Be String`).

    Following keywords from ``BuiltIn`` library can also be used with strings:

    - `Catenate`
    - `Get Length`
    - `Length Should Be`
    - `Should (Not) Be Empty`
    - `Should (Not) Be Equal (As Strings/Integers/Numbers)`
    - `Should (Not) Match (Regexp)`
    - `Should (Not) Contain`
    - `Should (Not) Start With`
    - `Should (Not) End With`
    - `Convert To String`
    - `Convert To Bytes`
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = get_version()

    def convert_to_lower_case(self, string):
        """Converts string to lower case.

        Uses Python's standard
        [https://docs.python.org/library/stdtypes.html#str.lower|lower()]
        method.

        Examples:
        | ${str1} = | Convert To Lower Case | ABC |
        | ${str2} = | Convert To Lower Case | 1A2c3D |
        | Should Be Equal | ${str1} | abc |
        | Should Be Equal | ${str2} | 1a2c3d |
        """
        return string.lower()

    def convert_to_upper_case(self, string) -> str:
        """Converts string to upper case.

        Uses Python's standard
        [https://docs.python.org/library/stdtypes.html#str.upper|upper()]
        method.

        Examples:
        | ${str1} = | Convert To Upper Case | abc |
        | ${str2} = | Convert To Upper Case | 1a2C3d |
        | Should Be Equal | ${str1} | ABC |
        | Should Be Equal | ${str2} | 1A2C3D |
        """
        return string.upper()

    @keyword(types=None)
    def convert_to_title_case(self, string, exclude=None) -> str:
        """Converts string to title case.

        Uses the following algorithm:

        - Split the string to words from whitespace characters (spaces,
          newlines, etc.).
        - Exclude words that are not all lower case. This preserves,
          for example, "OK" and "iPhone".
        - Exclude also words listed in the optional ``exclude`` argument.
        - Title case the first alphabetical character of each word that has
          not been excluded.
        - Join all words together so that original whitespace is preserved.

        Explicitly excluded words can be given as a list or as a string with
        words separated by a comma and an optional space. Excluded words are
        actually considered to be regular expression patterns, so it is
        possible to use something like "example[.!?]?" to match the word
        "example" on it own and also if followed by ".", "!" or "?".
        See `BuiltIn.Should Match Regexp` for more information about Python
        regular expression syntax in general and how to use it in Robot
        Framework data in particular.

        Examples:
        | ${str1} = | Convert To Title Case | hello, world!     |
        | ${str2} = | Convert To Title Case | it's an OK iPhone | exclude=a, an, the |
        | ${str3} = | Convert To Title Case | distance is 1 km. | exclude=is, km.? |
        | Should Be Equal | ${str1} | Hello, World! |
        | Should Be Equal | ${str2} | It's an OK iPhone |
        | Should Be Equal | ${str3} | Distance is 1 km. |

        The reason this keyword does not use Python's standard
        [https://docs.python.org/library/stdtypes.html#str.title|title()]
        method is that it can yield undesired results, for example, if
        strings contain upper case letters or special characters like
        apostrophes. It would, for example, convert "it's an OK iPhone"
        to "It'S An Ok Iphone".
        """
        if not isinstance(string, str):
            raise TypeError("This keyword works only with strings.")
        if isinstance(exclude, str):
            exclude = [e.strip() for e in exclude.split(",")]
        elif not exclude:
            exclude = []
        exclude = [re.compile(f"^{e}$") for e in exclude]

        def title(word):
            if any(e.match(word) for e in exclude) or not word.islower():
                return word
            for index, char in enumerate(word):
                if char.isalpha():
                    return word[:index] + word[index].title() + word[index + 1 :]
            return word

        tokens = re.split(r"(\s+)", string, flags=re.UNICODE)
        return "".join(title(token) for token in tokens)

    def encode_string_to_bytes(self, string, encoding, errors="strict") -> bytes:
        """Encodes the given ``string`` to bytes using the given ``encoding``.

        ``errors`` argument controls what to do if encoding some characters fails.
        All values accepted by ``encode`` method in Python are valid, but in
        practice the following values are most useful:

        - ``strict``: fail if characters cannot be encoded (default)
        - ``ignore``: ignore characters that cannot be encoded
        - ``replace``: replace characters that cannot be encoded with
          a replacement character

        Examples:
        | ${bytes} = | Encode String To Bytes | ${string} | UTF-8 |
        | ${bytes} = | Encode String To Bytes | ${string} | ASCII | errors=ignore |

        Use `Convert To Bytes` in ``BuiltIn`` if you want to create bytes based
        on character or integer sequences. Use `Decode Bytes To String` if you
        need to convert bytes to strings and `Convert To String`
        in ``BuiltIn`` if you need to convert arbitrary objects to strings.
        """
        return bytes(string.encode(encoding, errors))

    def decode_bytes_to_string(self, bytes, encoding, errors="strict") -> str:
        """Decodes the given ``bytes`` to a string using the given ``encoding``.

        ``errors`` argument controls what to do if decoding some bytes fails.
        All values accepted by ``decode`` method in Python are valid, but in
        practice the following values are most useful:

        - ``strict``: fail if characters cannot be decoded (default)
        - ``ignore``: ignore characters that cannot be decoded
        - ``replace``: replace characters that cannot be decoded with
          a replacement character

        Examples:
        | ${string} = | Decode Bytes To String | ${bytes} | UTF-8 |
        | ${string} = | Decode Bytes To String | ${bytes} | ASCII | errors=ignore |

        Use `Encode String To Bytes` if you need to convert strings to bytes,
        and `Convert To String` in ``BuiltIn`` if you need to
        convert arbitrary objects to strings.
        """
        if isinstance(bytes, str):
            raise TypeError("Cannot decode strings.")
        return bytes.decode(encoding, errors)

    def format_string(self, template, /, *positional, **named) -> str:
        """Formats a ``template`` using the given ``positional`` and ``named`` arguments.

        The template can be either be a string or an absolute path to
        an existing file. In the latter case the file is read and its contents
        are used as the template. If the template file contains non-ASCII
        characters, it must be encoded using UTF-8.

        The template is formatted using Python's
        [https://docs.python.org/library/string.html#format-string-syntax|format
        string syntax]. Placeholders are marked using ``{}`` with possible
        field name and format specification inside. Literal curly braces
        can be inserted by doubling them like `{{` and `}}`.

        Examples:
        | ${to} = | Format String | To: {} <{}>                    | ${user}      | ${email} |
        | ${to} = | Format String | To: {name} <{email}>           | name=${name} | email=${email} |
        | ${to} = | Format String | To: {user.name} <{user.email}> | user=${user} |
        | ${xx} = | Format String | {:*^30}                        | centered     |
        | ${yy} = | Format String | {0:{width}{base}}              | ${42}        | base=X | width=10 |
        | ${zz} = | Format String | ${CURDIR}/template.txt         | positional   | named=value |

        Prior to Robot Framework 7.1, possible equal signs in the template string must
        be escaped with a backslash like ``x\\={}`.
        """
        if os.path.isabs(template) and os.path.isfile(template):
            template = template.replace("/", os.sep)
            logger.info(
                f'Reading template from file <a href="{template}">{template}</a>.',
                html=True,
            )
            with FileReader(template) as reader:
                template = reader.read()
        return template.format(*positional, **named)

    def get_line_count(self, string) -> int:
        """Returns and logs the number of lines in the given string."""
        count = len(string.splitlines())
        logger.info(f"{count} lines.")
        return count

    def split_to_lines(self, string, start=0, end=None) -> list[str]:
        """Splits the given string to lines.

        It is possible to get only a selection of lines from ``start``
        to ``end`` so that ``start`` index is inclusive and ``end`` is
        exclusive. Line numbering starts from 0, and it is possible to
        use negative indices to refer to lines from the end.

        Lines are returned without the newlines. The number of
        returned lines is automatically logged.

        Examples:
        | @{lines} =        | Split To Lines | ${manylines} |    |    |
        | @{ignore first} = | Split To Lines | ${manylines} | 1  |    |
        | @{ignore last} =  | Split To Lines | ${manylines} |    | -1 |
        | @{5th to 10th} =  | Split To Lines | ${manylines} | 4  | 10 |
        | @{first two} =    | Split To Lines | ${manylines} |    | 1  |
        | @{last two} =     | Split To Lines | ${manylines} | -2 |    |

        Use `Get Line` if you only need to get a single line.
        """
        start = self._convert_to_index(start, "start")
        end = self._convert_to_index(end, "end")
        lines = string.splitlines()[start:end]
        logger.info(f"{len(lines)} line{s(lines)} returned.")
        return lines

    def get_line(self, string, line_number) -> str:
        """Returns the specified line from the given ``string``.

        Line numbering starts from 0, and it is possible to use
        negative indices to refer to lines from the end. The line is
        returned without the newline character.

        Examples:
        | ${first} =    | Get Line | ${string} | 0  |
        | ${2nd last} = | Get Line | ${string} | -2 |

        Use `Split To Lines` if all lines are needed.
        """
        line_number = self._convert_to_integer(line_number, "line_number")
        return string.splitlines()[line_number]

    def get_lines_containing_string(
        self,
        string: str,
        pattern: str,
        case_insensitive: "bool|None" = None,
        ignore_case: bool = False,
    ) -> str:
        """Returns lines of the given ``string`` that contain the ``pattern``.

        The ``pattern`` is always considered to be a normal string, not a glob
        or regexp pattern. A line matches if the ``pattern`` is found anywhere
        on it.

        The match is case-sensitive by default, but that can be changed by
        giving ``ignore_case`` a true value. This option is new in Robot
        Framework 7.0, but with older versions it is possible to use the
        nowadays deprecated ``case_insensitive`` argument.

        Lines are returned as a string with lines joined together with
        a newline. Possible trailing newline is never returned. The number
        of matching lines is automatically logged.

        Examples:
        | ${lines} = | Get Lines Containing String | ${result} | An example |
        | ${ret} =   | Get Lines Containing String | ${ret} | FAIL | ignore_case=True |

        See `Get Lines Matching Pattern` and `Get Lines Matching Regexp`
        if you need more complex pattern matching.
        """
        if case_insensitive is not None:
            ignore_case = case_insensitive
        if ignore_case:
            pattern = pattern.casefold()
            contains = lambda line: pattern in line.casefold()
        else:
            contains = lambda line: pattern in line
        return self._get_matching_lines(string, contains)

    def get_lines_matching_pattern(
        self,
        string: str,
        pattern: str,
        case_insensitive: "bool|None" = None,
        ignore_case: bool = False,
    ) -> str:
        """Returns lines of the given ``string`` that match the ``pattern``.

        The ``pattern`` is a _glob pattern_ where:
        | ``*``        | matches everything |
        | ``?``        | matches any single character |
        | ``[chars]``  | matches any character inside square brackets (e.g. ``[abc]`` matches either ``a``, ``b`` or ``c``) |
        | ``[!chars]`` | matches any character not inside square brackets |

        A line matches only if it matches the ``pattern`` fully.

        The match is case-sensitive by default, but that can be changed by
        giving ``ignore_case`` a true value. This option is new in Robot
        Framework 7.0, but with older versions it is possible to use the
        nowadays deprecated ``case_insensitive`` argument.

        Lines are returned as a string with lines joined together with
        a newline. Possible trailing newline is never returned. The number
        of matching lines is automatically logged.

        Examples:
        | ${lines} = | Get Lines Matching Pattern | ${result} | Wild???? example |
        | ${ret} = | Get Lines Matching Pattern | ${ret} | FAIL: * | ignore_case=True |

        See `Get Lines Matching Regexp` if you need more complex
        patterns and `Get Lines Containing String` if searching
        literal strings is enough.
        """
        if case_insensitive is not None:
            ignore_case = case_insensitive
        if ignore_case:
            pattern = pattern.casefold()
            matches = lambda line: fnmatchcase(line.casefold(), pattern)
        else:
            matches = lambda line: fnmatchcase(line, pattern)
        return self._get_matching_lines(string, matches)

    def get_lines_matching_regexp(
        self,
        string,
        pattern,
        partial_match=False,
        flags=None,
    ) -> str:
        """Returns lines of the given ``string`` that match the regexp ``pattern``.

        See `BuiltIn.Should Match Regexp` for more information about
        Python regular expression syntax in general and how to use it
        in Robot Framework data in particular.

        Lines match only if they match the pattern fully by default, but
        partial matching can be enabled by giving the ``partial_match``
        argument a true value.

        If the pattern is empty, it matches only empty lines by default.
        When partial matching is enabled, empty pattern matches all lines.

        Possible flags altering how the expression is parsed (e.g. ``re.IGNORECASE``,
        ``re.VERBOSE``) can be given using the ``flags`` argument (e.g.
        ``flags=IGNORECASE | VERBOSE``) or embedded to the pattern (e.g.
        ``(?ix)pattern``).

        Lines are returned as one string concatenated back together with
        newlines. Possible trailing newline is never returned. The
        number of matching lines is automatically logged.

        Examples:
        | ${lines} = | Get Lines Matching Regexp | ${result} | Reg\\\\w{3} example |
        | ${lines} = | Get Lines Matching Regexp | ${result} | Reg\\\\w{3} example | partial_match=true |
        | ${ret} =   | Get Lines Matching Regexp | ${ret}    | (?i)FAIL: .* |
        | ${ret} =   | Get Lines Matching Regexp | ${ret}    | FAIL: .* | flags=IGNORECASE |

        See `Get Lines Matching Pattern` and `Get Lines Containing String` if you
        do not need the full regular expression powers (and complexity).

        The ``flags`` argument is new in Robot Framework 6.0.
        """
        regexp = re.compile(pattern, flags=parse_re_flags(flags))
        match = regexp.search if partial_match else regexp.fullmatch
        return self._get_matching_lines(string, match)

    def _get_matching_lines(self, string, matches) -> str:
        lines = string.splitlines()
        matching = [line for line in lines if matches(line)]
        logger.info(f"{len(matching)} out of {len(lines)} lines matched.")
        return "\n".join(matching)

    def get_regexp_matches(self, string, pattern, *groups, flags=None) -> list[str]:
        """Returns a list of all non-overlapping matches in the given string.

        ``string`` is the string to find matches from and ``pattern`` is the
        regular expression. See `BuiltIn.Should Match Regexp` for more
        information about Python regular expression syntax in general and how
        to use it in Robot Framework data in particular.

        If no groups are used, the returned list contains full matches. If one
        group is used, the list contains only contents of that group. If
        multiple groups are used, the list contains tuples that contain
        individual group contents. All groups can be given as indexes (starting
        from 1) and named groups also as names.

        Possible flags altering how the expression is parsed (e.g. ``re.IGNORECASE``,
        ``re.MULTILINE``) can be given using the ``flags`` argument (e.g.
        ``flags=IGNORECASE | MULTILINE``) or embedded to the pattern (e.g.
        ``(?im)pattern``).

        Examples:
        | ${no match} =    | Get Regexp Matches | the string | xxx     |
        | ${matches} =     | Get Regexp Matches | the string | t..     |
        | ${matches} =     | Get Regexp Matches | the string | T..     | flags=IGNORECASE |
        | ${one group} =   | Get Regexp Matches | the string | t(..)   | 1 |
        | ${named group} = | Get Regexp Matches | the string | t(?P<name>..) | name |
        | ${two groups} =  | Get Regexp Matches | the string | t(.)(.) | 1 | 2 |
        =>
        | ${no match} = []
        | ${matches} = ['the', 'tri']
        | ${one group} = ['he', 'ri']
        | ${named group} = ['he', 'ri']
        | ${two groups} = [('h', 'e'), ('r', 'i')]

        The ``flags`` argument is new in Robot Framework 6.0.
        """
        regexp = re.compile(pattern, flags=parse_re_flags(flags))
        groups = [self._parse_group(g) for g in groups]
        return [m.group(*groups) for m in regexp.finditer(string)]

    def _parse_group(self, group):
        try:
            return int(group)
        except ValueError:
            return group

    def replace_string(self, string, search_for, replace_with, count=-1) -> str:
        """Replaces ``search_for`` in the given ``string`` with ``replace_with``.

        ``search_for`` is used as a literal string. See `Replace String
        Using Regexp` if more powerful pattern matching is needed.
        If you need to just remove a string see `Remove String`.

        If the optional argument ``count`` is given, only that many
        occurrences from left are replaced. Negative ``count`` means
        that all occurrences are replaced (default behaviour) and zero
        means that nothing is done.

        A modified version of the string is returned and the original
        string is not altered.

        Examples:
        | ${str} =        | Replace String | Hello, world!  | world | tellus   |
        | Should Be Equal | ${str}         | Hello, tellus! |       |          |
        | ${str} =        | Replace String | Hello, world!  | l     | ${EMPTY} | count=1 |
        | Should Be Equal | ${str}         | Helo, world!   |       |          |
        """
        count = self._convert_to_integer(count, "count")
        return string.replace(search_for, replace_with, count)

    def replace_string_using_regexp(
        self,
        string,
        pattern,
        replace_with,
        count=-1,
        flags=None,
    ) -> str:
        """Replaces ``pattern`` in the given ``string`` with ``replace_with``.

        This keyword is otherwise identical to `Replace String`, but
        the ``pattern`` to search for is considered to be a regular
        expression.  See `BuiltIn.Should Match Regexp` for more
        information about Python regular expression syntax in general
        and how to use it in Robot Framework data in particular.

        Possible flags altering how the expression is parsed (e.g. ``re.IGNORECASE``,
        ``re.MULTILINE``) can be given using the ``flags`` argument (e.g.
        ``flags=IGNORECASE | MULTILINE``) or embedded to the pattern (e.g.
        ``(?im)pattern``).

        If you need to just remove a string see `Remove String Using Regexp`.

        Examples:
        | ${str} = | Replace String Using Regexp | ${str} | 20\\\\d\\\\d-\\\\d\\\\d-\\\\d\\\\d | <DATE> |
        | ${str} = | Replace String Using Regexp | ${str} | (Hello|Hi) | ${EMPTY} | count=1 |

        The ``flags`` argument is new in Robot Framework 6.0.
        """
        count = self._convert_to_integer(count, "count")
        # re.sub handles 0 and negative counts differently than string.replace
        if count == 0:
            return string
        return re.sub(
            pattern,
            replace_with,
            string,
            count=max(count, 0),
            flags=parse_re_flags(flags),
        )

    def remove_string(self, string, *removables) -> str:
        """Removes all ``removables`` from the given ``string``.

        ``removables`` are used as literal strings. Each removable will be
        matched to a temporary string from which preceding removables have
        been already removed. See second example below.

        Use `Remove String Using Regexp` if more powerful pattern matching is
        needed. If only a certain number of matches should be removed,
        `Replace String` or `Replace String Using Regexp` can be used.

        A modified version of the string is returned and the original
        string is not altered.

        Examples:
        | ${str} =        | Remove String | Robot Framework | work   |
        | Should Be Equal | ${str}        | Robot Frame     |
        | ${str} =        | Remove String | Robot Framework | o | bt |
        | Should Be Equal | ${str}        | R Framewrk      |
        """
        for removable in removables:
            string = self.replace_string(string, removable, "")
        return string

    def remove_string_using_regexp(self, string, *patterns, flags=None) -> str:
        """Removes ``patterns`` from the given ``string``.

        This keyword is otherwise identical to `Remove String`, but
        the ``patterns`` to search for are considered to be a regular
        expression. See `Replace String Using Regexp` for more information
        about the regular expression syntax. That keyword can also be
        used if there is a need to remove only a certain number of
        occurrences.

        Possible flags altering how the expression is parsed (e.g. ``re.IGNORECASE``,
        ``re.MULTILINE``) can be given using the ``flags`` argument (e.g.
        ``flags=IGNORECASE | MULTILINE``) or embedded to the pattern (e.g.
        ``(?im)pattern``).

        The ``flags`` argument is new in Robot Framework 6.0.
        """
        for pattern in patterns:
            string = self.replace_string_using_regexp(string, pattern, "", flags=flags)
        return string

    @keyword(types=None)
    def split_string(self, string, separator=None, max_split=-1) -> list[str]:
        """Splits the ``string`` using ``separator`` as a delimiter string.

        If a ``separator`` is not given, any whitespace string is a
        separator. In that case also possible consecutive whitespace
        as well as leading and trailing whitespace is ignored.

        Split words are returned as a list. If the optional
        ``max_split`` is given, at most ``max_split`` splits are done, and
        the returned list will have maximum ``max_split + 1`` elements.

        Examples:
        | @{words} =         | Split String | ${string} |
        | @{words} =         | Split String | ${string} | ,${SPACE} |
        | ${pre} | ${post} = | Split String | ${string} | ::    | 1 |

        See `Split String From Right` if you want to start splitting
        from right, and `Fetch From Left` and `Fetch From Right` if
        you only want to get first/last part of the string.
        """
        if separator == "":
            separator = None
        max_split = self._convert_to_integer(max_split, "max_split")
        return string.split(separator, max_split)

    @keyword(types=None)
    def split_string_from_right(
        self, string, separator=None, max_split=-1
    ) -> list[str]:
        """Splits the ``string`` using ``separator`` starting from right.

        Same as `Split String`, but splitting is started from right. This has
        an effect only when ``max_split`` is given.

        Examples:
        | ${first} | ${rest} = | Split String            | ${string} | - | 1 |
        | ${rest}  | ${last} = | Split String From Right | ${string} | - | 1 |
        """
        if separator == "":
            separator = None
        max_split = self._convert_to_integer(max_split, "max_split")
        return string.rsplit(separator, max_split)

    def split_string_to_characters(self, string) -> list[str]:
        """Splits the given ``string`` to characters.

        Example:
        | @{characters} = | Split String To Characters | ${string} |
        """
        return list(string)

    def fetch_from_left(self, string, marker) -> str:
        """Returns contents of the ``string`` before the first occurrence of ``marker``.

        If the ``marker`` is not found, whole string is returned.

        See also `Fetch From Right`, `Split String` and `Split String
        From Right`.
        """
        return string.split(marker)[0]

    def fetch_from_right(self, string, marker) -> str:
        """Returns contents of the ``string`` after the last occurrence of ``marker``.

        If the ``marker`` is not found, whole string is returned.

        See also `Fetch From Left`, `Split String` and `Split String
        From Right`.
        """
        return string.split(marker)[-1]

    def generate_random_string(self, length=8, chars="[LETTERS][NUMBERS]") -> str:
        """Generates a string with a desired ``length`` from the given ``chars``.

        ``length`` can be given as a number, a string representation of a number,
        or as a range of numbers, such as ``5-10``. When a range of values is given
        the range will be selected by random within the range.

        The population sequence ``chars`` contains the characters to use
        when generating the random string. It can contain any
        characters, and it is possible to use special markers
        explained in the table below:

        |  = Marker =   |               = Explanation =                   |
        | ``[LOWER]``   | Lowercase ASCII characters from ``a`` to ``z``. |
        | ``[UPPER]``   | Uppercase ASCII characters from ``A`` to ``Z``. |
        | ``[LETTERS]`` | Lowercase and uppercase ASCII characters.       |
        | ``[NUMBERS]`` | Numbers from 0 to 9.                            |

        Examples:
        | ${ret} = | Generate Random String |
        | ${low} = | Generate Random String | 12 | [LOWER]         |
        | ${bin} = | Generate Random String | 8  | 01              |
        | ${hex} = | Generate Random String | 4  | [NUMBERS]abcdef |
        | ${rnd} = | Generate Random String | 5-10 | # Generates a string 5 to 10 characters long |

        Giving ``length`` as a range of values is new in Robot Framework 5.0.
        """
        if length == "":
            length = 8
        if isinstance(length, str) and re.match(r"^\d+-\d+$", length):
            min_length, max_length = length.split("-")
            length = randint(
                self._convert_to_integer(min_length, "length"),
                self._convert_to_integer(max_length, "length"),
            )
        else:
            length = self._convert_to_integer(length, "length")
        for name, value in [
            ("[LOWER]", ascii_lowercase),
            ("[UPPER]", ascii_uppercase),
            ("[LETTERS]", ascii_lowercase + ascii_uppercase),
            ("[NUMBERS]", digits),
        ]:
            chars = chars.replace(name, value)
        maxi = len(chars) - 1
        return "".join(chars[randint(0, maxi)] for _ in range(length))

    def get_substring(self, string, start, end=None) -> str:
        """Returns a substring from ``start`` index to ``end`` index.

        The ``start`` index is inclusive and ``end`` is exclusive.
        Indexing starts from 0, and it is possible to use
        negative indices to refer to characters from the end.

        Examples:
        | ${ignore first} = | Get Substring | ${string} | 1  |    |
        | ${ignore last} =  | Get Substring | ${string} | 0  | -1 |
        | ${5th to 10th} =  | Get Substring | ${string} | 4  | 10 |
        | ${first two} =    | Get Substring | ${string} | 0  | 1  |
        | ${last two} =     | Get Substring | ${string} | -2 |    |
        """
        start = self._convert_to_index(start, "start")
        end = self._convert_to_index(end, "end")
        return string[start:end]

    @keyword(types=None)
    def strip_string(self, string, mode="both", characters=None) -> str:
        """Remove leading and/or trailing whitespaces from the given string.

        ``mode`` is either ``left`` to remove leading characters, ``right`` to
        remove trailing characters, ``both`` (default) to remove the
        characters from both sides of the string or ``none`` to return the
        unmodified string.

        If the optional ``characters`` is given, it must be a string and the
        characters in the string will be stripped in the string. Please note,
        that this is not a substring to be removed but a list of characters,
        see the example below.

        Examples:
        | ${stripped}=  | Strip String | ${SPACE}Hello${SPACE} | |
        | Should Be Equal | ${stripped} | Hello | |
        | ${stripped}=  | Strip String | ${SPACE}Hello${SPACE} | mode=left |
        | Should Be Equal | ${stripped} | Hello${SPACE} | |
        | ${stripped}=  | Strip String | aabaHelloeee | characters=abe |
        | Should Be Equal | ${stripped} | Hello | |
        """
        try:
            method = {
                "BOTH": string.strip,
                "LEFT": string.lstrip,
                "RIGHT": string.rstrip,
                "NONE": lambda characters: string,
            }[mode.upper()]
        except KeyError:
            raise ValueError(f"Invalid mode '{mode}'.")
        return method(characters)

    def should_be_string(self, item, msg=None):
        """Fails if the given ``item`` is not a string.

        The default error message can be overridden with the optional ``msg`` argument.
        """
        if not isinstance(item, str):
            raise AssertionError(msg or f"{item!r} is {type_name(item)}, not a string.")

    def should_not_be_string(self, item, msg=None):
        """Fails if the given ``item`` is a string.

        The default error message can be overridden with the optional ``msg`` argument.
        """
        if isinstance(item, str):
            raise AssertionError(msg or f"{item!r} is a string.")

    def should_be_unicode_string(self, item, msg=None):
        """Fails if the given ``item`` is not a Unicode string.

        On Python 3 this keyword behaves exactly the same way `Should Be String`.
        That keyword should be used instead and this keyword will be deprecated.
        """
        self.should_be_string(item, msg)

    def should_be_byte_string(self, item, msg=None):
        """Fails if the given ``item`` is not a byte string.

        Use `Should Be String` if you want to verify the ``item`` is a string.

        The default error message can be overridden with the optional ``msg`` argument.
        """
        if not isinstance(item, bytes):
            raise AssertionError(msg or f"{item!r} is not a byte string.")

    def should_be_lower_case(self, string, msg=None):
        """Fails if the given ``string`` is not in lower case.

        For example, ``'string'`` and ``'with specials!'`` would pass, and
        ``'String'``, ``''`` and ``' '`` would fail.

        The default error message can be overridden with the optional
        ``msg`` argument.

        See also `Should Be Upper Case` and `Should Be Title Case`.
        """
        if not string.islower():
            raise AssertionError(msg or f"{string!r} is not lower case.")

    def should_be_upper_case(self, string, msg=None):
        """Fails if the given ``string`` is not in upper case.

        For example, ``'STRING'`` and ``'WITH SPECIALS!'`` would pass, and
        ``'String'``, ``''`` and ``' '`` would fail.

        The default error message can be overridden with the optional
        ``msg`` argument.

        See also `Should Be Title Case` and `Should Be Lower Case`.
        """
        if not string.isupper():
            raise AssertionError(msg or f"{string!r} is not upper case.")

    @keyword(types=None)
    def should_be_title_case(self, string, msg=None, exclude=None):
        """Fails if given ``string`` is not title.

        ``string`` is a title cased string if there is at least one upper case
        letter in each word.

        For example, ``'This Is Title'`` and ``'OK, Give Me My iPhone'``
        would pass. ``'all words lower'`` and ``'Word In lower'`` would fail.

        This logic changed in Robot Framework 4.0 to be compatible with
        `Convert to Title Case`. See `Convert to Title Case` for title case
        algorithm and reasoning.

        The default error message can be overridden with the optional
        ``msg`` argument.

        Words can be explicitly excluded with the optional ``exclude`` argument.

        Explicitly excluded words can be given as a list or as a string with
        words separated by a comma and an optional space. Excluded words are
        actually considered to be regular expression patterns, so it is
        possible to use something like "example[.!?]?" to match the word
        "example" on it own and also if followed by ".", "!" or "?".
        See `BuiltIn.Should Match Regexp` for more information about Python
        regular expression syntax in general and how to use it in Robot
        Framework data in particular.

        See also `Should Be Upper Case` and `Should Be Lower Case`.
        """
        if string != self.convert_to_title_case(string, exclude):
            raise AssertionError(msg or f"{string!r} is not title case.")

    def _convert_to_index(self, value, name) -> int | None:
        if value == "":
            return 0
        if value is None:
            return None
        return self._convert_to_integer(value, name)

    def _convert_to_integer(self, value, name) -> int:
        try:
            return int(value)
        except ValueError:
            raise ValueError(
                f"Cannot convert {name!r} argument {value!r} to an integer."
            )
