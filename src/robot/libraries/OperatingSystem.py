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

import fnmatch
import glob
import os
import pathlib
import re
import shutil
import tempfile
import time
from datetime import datetime

from robot.api import logger
from robot.api.deco import keyword
from robot.utils import (
    abspath, ConnectionCache, console_decode, CONSOLE_ENCODING, del_env_var,
    get_env_var, get_env_vars, get_time, normpath, parse_time, plural_or_not as s,
    PY_VERSION, safe_str, secs_to_timestr, seq2str, set_env_var, timestr_to_secs,
    WINDOWS
)
from robot.version import get_version

__version__ = get_version()
PROCESSES = ConnectionCache("No active processes.")


class OperatingSystem:
    r"""A library providing keywords for operating system related tasks.

    ``OperatingSystem`` is Robot Framework's standard library that
    enables various operating system related tasks to be performed in
    the system where Robot Framework is running. It can, among other
    things, execute commands (e.g. `Run`), create and remove files and
    directories (e.g. `Create File`, `Remove Directory`), check
    whether files or directories exists or contain something
    (e.g. `File Should Exist`, `Directory Should Be Empty`) and
    manipulate environment variables (e.g. `Set Environment Variable`).

    == Table of contents ==

    %TOC%

    = Path separators =

    Because Robot Framework uses the backslash (``\``) as an escape character
    in its data, using a literal backslash requires duplicating it like
    in ``c:\\path\\file.txt``. That can be inconvenient especially with
    longer Windows paths, and thus all keywords expecting paths as arguments
    convert forward slashes to backslashes automatically on Windows. This also
    means that paths like ``${CURDIR}/path/file.txt`` are operating system
    independent.

    Notice that the automatic path separator conversion does not work if
    the path is only a part of an argument like with the `Run` keyword.
    In these cases the built-in variable ``${/}`` that contains ``\`` or ``/``,
    depending on the operating system, can be used instead.

    = Pattern matching =

    Many keywords accept arguments as either _glob_ or _regular expression_ patterns.

    == Glob patterns ==

    Some keywords, for example `List Directory`, support so called
    [http://en.wikipedia.org/wiki/Glob_(programming)|glob patterns] where:

    | ``*``        | matches any string, even an empty string                |
    | ``?``        | matches any single character                            |
    | ``[chars]``  | matches one character in the bracket                    |
    | ``[!chars]`` | matches one character not in the bracket                |
    | ``[a-z]``    | matches one character from the range in the bracket     |
    | ``[!a-z]``   | matches one character not from the range in the bracket |

    Unless otherwise noted, matching is case-insensitive on case-insensitive
    operating systems such as Windows.

    == Regular expressions ==

    Some keywords, for example `Grep File`, support
    [http://en.wikipedia.org/wiki/Regular_expression|regular expressions]
    that are more powerful but also more complicated that glob patterns.
    The regular expression support is implemented using Python's
    [http://docs.python.org/library/re.html|re module] and its documentation
    should be consulted for more information about the syntax.

    Because the backslash character (``\``) is an escape character in
    Robot Framework data, possible backslash characters in regular
    expressions need to be escaped with another backslash like ``\\d\\w+``.
    Strings that may contain special characters but should be handled
    as literal strings, can be escaped with the `Regexp Escape` keyword
    from the BuiltIn library.

    = Tilde expansion =

    Paths beginning with ``~`` or ``~username`` are expanded to the current or
    specified user's home directory, respectively. The resulting path is
    operating system dependent, but typically e.g. ``~/robot`` is expanded to
    ``C:\Users\<user>\robot`` on Windows and ``/home/<user>/robot`` on Unixes.

    = pathlib.Path support =

    Starting from Robot Framework 6.0, arguments representing paths can be given
    as [https://docs.python.org/3/library/pathlib.html|pathlib.Path] instances
    in addition to strings.

    All keywords returning paths return them as strings. This may change in
    the future so that the return value type matches the argument type.

    = Boolean arguments =

    Some keywords accept arguments that are handled as Boolean values true or
    false. If such an argument is given as a string, it is considered false if
    it is an empty string or equal to ``FALSE``, ``NONE``, ``NO``, ``OFF`` or
    ``0``, case-insensitively. Other strings are considered true regardless
    their value, and other argument types are tested using the same
    [http://docs.python.org/library/stdtypes.html#truth|rules as in Python].

    True examples:
    | `Remove Directory` | ${path} | recursive=True    | # Strings are generally true.    |
    | `Remove Directory` | ${path} | recursive=yes     | # Same as the above.             |
    | `Remove Directory` | ${path} | recursive=${TRUE} | # Python ``True`` is true.       |
    | `Remove Directory` | ${path} | recursive=${42}   | # Numbers other than 0 are true. |

    False examples:
    | `Remove Directory` | ${path} | recursive=False    | # String ``false`` is false.   |
    | `Remove Directory` | ${path} | recursive=no       | # Also string ``no`` is false. |
    | `Remove Directory` | ${path} | recursive=${EMPTY} | # Empty string is false.       |
    | `Remove Directory` | ${path} | recursive=${FALSE} | # Python ``False`` is false.   |

    = Example =

    | ***** Settings *****
    | Library         OperatingSystem
    |
    | ***** Variables *****
    | ${PATH}         ${CURDIR}/example.txt
    |
    | ***** Test Cases *****
    | Example
    |     `Create File`          ${PATH}    Some text
    |     `File Should Exist`    ${PATH}
    |     `Copy File`            ${PATH}    ~/file.txt
    """

    ROBOT_LIBRARY_SCOPE = "GLOBAL"
    ROBOT_LIBRARY_VERSION = __version__

    def run(self, command) -> str:
        """Runs the given command in the system and returns the output.

        The execution status of the command *is not checked* by this
        keyword, and it must be done separately based on the returned
        output. If the execution return code is needed, either `Run
        And Return RC` or `Run And Return RC And Output` can be used.

        The standard error stream is automatically redirected to the standard
        output stream by adding ``2>&1`` after the executed command. This
        automatic redirection is done only when the executed command does not
        contain additional output redirections. You can thus freely forward
        the standard error somewhere else, for example, like
        ``my_command 2>stderr.txt``.

        The returned output contains everything written into the standard
        output or error streams by the command (unless either of them
        is redirected explicitly). Many commands add an extra newline
        (``\\n``) after the output to make it easier to read in the
        console. To ease processing the returned output, this possible
        trailing newline is stripped by this keyword.

        Examples:
        | ${output} =        | Run       | ls -lhF /tmp |
        | Log                | ${output} |
        | ${result} =        | Run       | ${CURDIR}${/}tester.py arg1 arg2 |
        | Should Not Contain | ${result} | FAIL |
        | ${stdout} =        | Run       | /opt/script.sh 2>/tmp/stderr.txt |
        | Should Be Equal    | ${stdout} | TEST PASSED |
        | File Should Be Empty | /tmp/stderr.txt |

        *TIP:* `Run Process` keyword provided by the
        [http://robotframework.org/robotframework/latest/libraries/Process.html|
        Process library] supports better process configuration and is generally
        recommended as a replacement for this keyword.
        """
        return self._run(command)[1]

    def run_and_return_rc(self, command) -> int:
        """Runs the given command in the system and returns the return code.

        The return code (RC) is returned as a positive integer in
        range from 0 to 255 as returned by the executed command. On
        some operating systems (notable Windows) original return codes
        can be something else, but this keyword always maps them to
        the 0-255 range. Since the RC is an integer, it must be
        checked e.g. with the keyword `Should Be Equal As Integers`
        instead of `Should Be Equal` (both are built-in keywords).

        Examples:
        | ${rc} = | Run and Return RC | ${CURDIR}${/}script.py arg |
        | Should Be Equal As Integers | ${rc} | 0 |
        | ${rc} = | Run and Return RC | /path/to/example.rb arg1 arg2 |
        | Should Be True | 0 < ${rc} < 42 |

        See `Run` and `Run And Return RC And Output` if you need to get the
        output of the executed command.

        *TIP:* `Run Process` keyword provided by the
        [http://robotframework.org/robotframework/latest/libraries/Process.html|
        Process library] supports better process configuration and is generally
        recommended as a replacement for this keyword.
        """
        return self._run(command)[0]

    def run_and_return_rc_and_output(self, command) -> tuple[int, str]:
        """Runs the given command in the system and returns the RC and output.

        The return code (RC) is returned similarly as with `Run And Return RC`
        and the output similarly as with `Run`.

        Examples:
        | ${rc} | ${output} =  | Run and Return RC and Output | ${CURDIR}${/}mytool |
        | Should Be Equal As Integers | ${rc}    | 0    |
        | Should Not Contain   | ${output}       | FAIL |
        | ${rc} | ${stdout} =  | Run and Return RC and Output | /opt/script.sh 2>/tmp/stderr.txt |
        | Should Be True       | ${rc} > 42      |
        | Should Be Equal      | ${stdout}       | TEST PASSED |
        | File Should Be Empty | /tmp/stderr.txt |

        *TIP:* `Run Process` keyword provided by the
        [http://robotframework.org/robotframework/latest/libraries/Process.html|
        Process library] supports better process configuration and is generally
        recommended as a replacement for this keyword.
        """
        return self._run(command)

    def _run(self, command):
        process = _Process(command)
        self._info(f"Running command '{process}'.")
        stdout = process.read()
        rc = process.close()
        return rc, stdout

    def get_file(self, path, encoding="UTF-8", encoding_errors="strict") -> str:
        """Returns the contents of a specified file.

        This keyword reads the specified file and returns the contents.
        Line breaks in content are converted to platform independent form.
        See also `Get Binary File`.

        ``encoding`` defines the encoding of the file. The default value is
        ``UTF-8``, which means that UTF-8 and ASCII encoded files are read
        correctly. In addition to the encodings supported by the underlying
        Python implementation, the following special encoding values can be
        used:

        - ``SYSTEM``: Use the default system encoding.
        - ``CONSOLE``: Use the console encoding. Outside Windows this is same
          as the system encoding.

        ``encoding_errors`` argument controls what to do if decoding some bytes
        fails. All values accepted by ``decode`` method in Python are valid, but
        in practice the following values are most useful:

        - ``strict``: Fail if characters cannot be decoded (default).
        - ``ignore``: Ignore characters that cannot be decoded.
        - ``replace``: Replace characters that cannot be decoded with
          a replacement character.
        """
        path = self._absnorm(path)
        self._link("Getting file '%s'.", path)
        encoding = self._map_encoding(encoding)
        # Using `newline=None` (default) and not converting `\r\n` -> `\n`
        # ourselves would be better but some of our own acceptance tests
        # depend on these semantics. Best solution would probably be making
        # `newline` configurable.
        # FIXME: Make `newline` configurable or at least submit an issue about that.
        with open(path, encoding=encoding, errors=encoding_errors, newline="") as f:
            return f.read().replace("\r\n", "\n")

    def _map_encoding(self, encoding):
        return {
            "SYSTEM": "locale" if PY_VERSION > (3, 10) else None,
            "CONSOLE": CONSOLE_ENCODING,
        }.get(encoding.upper(), encoding)

    def get_binary_file(self, path) -> bytes:
        """Returns the contents of a specified file.

        This keyword reads the specified file and returns the contents as is.
        See also `Get File`.
        """
        path = self._absnorm(path)
        self._link("Getting file '%s'.", path)
        with open(path, "rb") as f:
            return f.read()

    def grep_file(
        self,
        path,
        pattern,
        encoding="UTF-8",
        encoding_errors="strict",
        regexp=False,
    ) -> str:
        r"""Returns the lines of the specified file that match the ``pattern``.

        This keyword reads a file from the file system using the defined
        ``path``, ``encoding`` and ``encoding_errors`` similarly as `Get File`.
        A difference is that only the lines that match the given ``pattern`` are
        returned. Lines are returned as a single string concatenated back together
        with newlines and the number of matched lines is automatically logged.
        Possible trailing newline is never returned.

        A line matches if it contains the ``pattern`` anywhere in it i.e. it does
        not need to match the pattern fully. There are two supported pattern types:

        - By default the pattern is considered a _glob_ pattern where, for example,
          ``*`` and ``?`` can be used as wildcards.
        - If the ``regexp`` argument is given a true value, the pattern is
          considered to be a _regular expression_. These patterns are more
          powerful but also more complicated than glob patterns. They often use
          the backslash character and it needs to be escaped in Robot Framework
          date like `\\`.

        For more information about glob and regular expression syntax, see
        the `Pattern matching` section. With this keyword matching is always
        case-sensitive.

        Examples:
        | ${errors} = | Grep File | /var/log/myapp.log | ERROR |
        | ${ret} = | Grep File | ${CURDIR}/file.txt | [Ww]ildc??d ex*ple |
        | ${ret} = | Grep File | ${CURDIR}/file.txt | [Ww]ildc\\w+d ex.*ple | regexp=True |

        Special encoding values ``SYSTEM`` and ``CONSOLE`` that `Get File` supports
        are supported by this keyword only with Robot Framework 4.0 and newer.

        Support for regular expressions is new in Robot Framework 5.0.
        """
        path = self._absnorm(path)
        if not regexp:
            pattern = fnmatch.translate(f"{pattern}*")
        reobj = re.compile(pattern)
        encoding = self._map_encoding(encoding)
        lines = []
        total_lines = 0
        self._link("Reading file '%s'.", path)
        with open(path, encoding=encoding, errors=encoding_errors) as file:
            for line in file:
                total_lines += 1
                line = line.rstrip("\r\n")
                if reobj.search(line):
                    lines.append(line)
            self._info(f"{len(lines)} out of {total_lines} lines matched.")
            return "\n".join(lines)

    def log_file(self, path, encoding="UTF-8", encoding_errors="strict") -> str:
        """Wrapper for `Get File` that also logs the returned file.

        The file is logged with the INFO level. If you want something else,
        just use `Get File` and the built-in keyword `Log` with the desired
        level.

        See `Get File` for more information about ``encoding`` and
        ``encoding_errors`` arguments.
        """
        content = self.get_file(path, encoding, encoding_errors)
        self._info(content)
        return content

    # File and directory existence

    def should_exist(self, path, msg=None):
        """Fails unless the given path (file or directory) exists.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        if not self._glob(path):
            self._fail(msg, f"Path '{path}' does not exist.")
        self._link("Path '%s' exists.", path)

    def should_not_exist(self, path, msg=None):
        """Fails if the given path (file or directory) exists.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        matches = self._glob(path)
        if matches:
            self._fail(msg, self._get_matches_error("Path", path, matches))
        self._link("Path '%s' does not exist.", path)

    def _glob(self, path):
        return glob.glob(path) if not os.path.exists(path) else [path]

    def _get_matches_error(self, kind, path, matches):
        if not self._is_glob_path(path):
            return f"{kind} '{path}' exists."
        return f"{kind} '{path}' matches {seq2str(sorted(matches))}."

    def _is_glob_path(self, path):
        return "*" in path or "?" in path or ("[" in path and "]" in path)

    def file_should_exist(self, path, msg=None):
        """Fails unless the given ``path`` points to an existing file.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        matches = [p for p in self._glob(path) if os.path.isfile(p)]
        if not matches:
            self._fail(msg, f"File '{path}' does not exist.")
        self._link("File '%s' exists.", path)

    def file_should_not_exist(self, path, msg=None):
        """Fails if the given path points to an existing file.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        matches = [p for p in self._glob(path) if os.path.isfile(p)]
        if matches:
            self._fail(msg, self._get_matches_error("File", path, matches))
        self._link("File '%s' does not exist.", path)

    def directory_should_exist(self, path, msg=None):
        """Fails unless the given path points to an existing directory.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        matches = [p for p in self._glob(path) if os.path.isdir(p)]
        if not matches:
            self._fail(msg, f"Directory '{path}' does not exist.")
        self._link("Directory '%s' exists.", path)

    def directory_should_not_exist(self, path, msg=None):
        """Fails if the given path points to an existing file.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        matches = [p for p in self._glob(path) if os.path.isdir(p)]
        if matches:
            self._fail(msg, self._get_matches_error("Directory", path, matches))
        self._link("Directory '%s' does not exist.", path)

    # Waiting file/dir to appear/disappear

    def wait_until_removed(self, path, timeout="1 minute"):
        """Waits until the given file or directory is removed.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.
        If the path is a pattern, the keyword waits until all matching
        items are removed.

        The optional ``timeout`` can be used to control the maximum time of
        waiting. The timeout is given as a timeout string, e.g. in a format
        ``15 seconds``, ``1min 10s`` or just ``10``. The time string format is
        described in an appendix of Robot Framework User Guide.

        If the timeout is negative, the keyword is never timed-out. The keyword
        returns immediately, if the path does not exist in the first place.
        """
        path = self._absnorm(path)
        timeout = timestr_to_secs(timeout)
        maxtime = time.time() + timeout
        while self._glob(path):
            if timeout >= 0 and time.time() > maxtime:
                self._fail(f"'{path}' was not removed in {secs_to_timestr(timeout)}.")
            time.sleep(0.1)
        self._link("'%s' was removed.", path)

    def wait_until_created(self, path, timeout="1 minute"):
        """Waits until the given file or directory is created.

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.
        If the path is a pattern, the keyword returns when an item matching
        it is created.

        The optional ``timeout`` can be used to control the maximum time of
        waiting. The timeout is given as a timeout string, e.g. in a format
        ``15 seconds``, ``1min 10s`` or just ``10``. The time string format is
        described in an appendix of Robot Framework User Guide.

        If the timeout is negative, the keyword is never timed-out. The keyword
        returns immediately, if the path already exists.
        """
        path = self._absnorm(path)
        timeout = timestr_to_secs(timeout)
        maxtime = time.time() + timeout
        while not self._glob(path):
            if timeout >= 0 and time.time() > maxtime:
                self._fail(f"'{path}' was not created in {secs_to_timestr(timeout)}.")
            time.sleep(0.1)
        self._link("'%s' was created.", path)

    # Dir/file empty

    def directory_should_be_empty(self, path, msg=None):
        """Fails unless the specified directory is empty.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        items = self._list_dir(path)
        if items:
            contents = seq2str(items, lastsep=", ")
            self._fail(msg, f"Directory '{path}' is not empty. Contents: {contents}.")
        self._link("Directory '%s' is empty.", path)

    def directory_should_not_be_empty(self, path, msg=None):
        """Fails if the specified directory is empty.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        items = self._list_dir(path)
        if not items:
            self._fail(msg, f"Directory '{path}' is empty.")
        self._link(f"Directory '%s' contains {len(items)} item{s(items)}.", path)

    def file_should_be_empty(self, path, msg=None):
        """Fails unless the specified file is empty.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        if not os.path.isfile(path):
            self._error(f"File '{path}' does not exist.")
        size = os.stat(path).st_size
        if size > 0:
            self._fail(msg, f"File '{path}' is not empty. Size: {size} byte{s(size)}.")
        self._link("File '%s' is empty.", path)

    def file_should_not_be_empty(self, path, msg=None):
        """Fails if the specified file is empty.

        The default error message can be overridden with the ``msg`` argument.
        """
        path = self._absnorm(path)
        if not os.path.isfile(path):
            self._error(f"File '{path}' does not exist.")
        size = os.stat(path).st_size
        if size == 0:
            self._fail(msg, f"File '{path}' is empty.")
        self._link(f"File '%s' contains {size} bytes.", path)

    # Creating and removing files and directory

    def create_file(self, path, content="", encoding="UTF-8"):
        """Creates a file with the given content and encoding.

        If the directory where the file is created does not exist, it is
        automatically created along with possible missing intermediate
        directories. Possible existing file is overwritten.

        On Windows newline characters (``\\n``) in content are automatically
        converted to Windows native newline sequence (``\\r\\n``).

        See `Get File` for more information about possible ``encoding`` values,
        including special values ``SYSTEM`` and ``CONSOLE``.

        Examples:
        | Create File | ${dir}/example.txt | Hello, world!       |         |
        | Create File | ${path}            | Hyv\\xe4 esimerkki  | Latin-1 |
        | Create File | /tmp/foo.txt       | 3\\nlines\\nhere\\n | SYSTEM  |

        Use `Append To File` if you want to append to an existing file
        and `Create Binary File` if you need to write bytes without encoding.
        `File Should Not Exist` can be used to avoid overwriting existing
        files.
        """
        path = self._write_to_file(path, content, encoding)
        self._link("Created file '%s'.", path)

    def _write_to_file(self, path, content, encoding=None, mode="w"):
        path = self._absnorm(path)
        parent = os.path.dirname(path)
        if not os.path.exists(parent):
            os.makedirs(parent)
        if encoding:
            encoding = self._map_encoding(encoding)
        with open(path, mode, encoding=encoding) as f:
            f.write(content)
        return path

    def create_binary_file(self, path, content):
        r"""Creates a binary file with the given content.

        If content is given as a Unicode string, it is first converted to bytes
        character by character. All characters with ordinal below 256 can be
        used and are converted to bytes with same values. Using characters
        with higher ordinal is an error.

        Byte strings, and possible other types, are written to the file as is.

        If the directory for the file does not exist, it is created, along
        with missing intermediate directories.

        Examples:
        | Create Binary File | ${dir}/example.png | ${image content} |
        | Create Binary File | ${path}            | \x01\x00\xe4\x00 |

        Use `Create File` if you want to create a text file using a certain
        encoding. `File Should Not Exist` can be used to avoid overwriting
        existing files.
        """
        if isinstance(content, str):
            content = bytes(ord(c) for c in content)
        path = self._write_to_file(path, content, mode="wb")
        self._link("Created binary file '%s'.", path)

    def append_to_file(self, path, content, encoding="UTF-8"):
        """Appends the given content to the specified file.

        If the file exists, the given text is written to its end. If the file
        does not exist, it is created.

        Other than not overwriting possible existing files, this keyword works
        exactly like `Create File`. See its documentation for more details
        about the usage.
        """
        path = self._write_to_file(path, content, encoding, mode="a")
        self._link("Appended to file '%s'.", path)

    def remove_file(self, path):
        """Removes a file with the given path.

        Passes if the file does not exist, but fails if the path does
        not point to a regular file (e.g. it points to a directory).

        The path can be given as an exact path or as a glob pattern.
        See the `Glob patterns` section for details about the supported syntax.
        If the path is a pattern, all files matching it are removed.
        """
        path = self._absnorm(path)
        matches = self._glob(path)
        if not matches:
            self._link("File '%s' does not exist.", path)
        for match in matches:
            if not os.path.isfile(match):
                self._error(f"Path '{path}' is not a file.")
            os.remove(match)
            self._link("Removed file '%s'.", match)

    def remove_files(self, *paths):
        """Uses `Remove File` to remove multiple files one-by-one.

        Example:
        | Remove Files | ${TEMPDIR}${/}foo.txt | ${TEMPDIR}${/}bar.txt | ${TEMPDIR}${/}zap.txt |
        """
        for path in paths:
            self.remove_file(path)

    def empty_directory(self, path):
        """Deletes all the content from the given directory.

        Deletes both files and sub-directories, but the specified directory
        itself if not removed. Use `Remove Directory` if you want to remove
        the whole directory.
        """
        path = self._absnorm(path)
        for item in self._list_dir(path, absolute=True):
            if os.path.isdir(item):
                shutil.rmtree(item)
            else:
                os.remove(item)
        self._link("Emptied directory '%s'.", path)

    def create_directory(self, path):
        """Creates the specified directory.

        Also possible intermediate directories are created. Passes if the
        directory already exists, but fails if the path exists and is not
        a directory.
        """
        path = self._absnorm(path)
        if os.path.isdir(path):
            self._link("Directory '%s' already exists.", path)
        elif os.path.exists(path):
            self._error(f"Path '{path}' is not a directory.")
        else:
            os.makedirs(path)
            self._link("Created directory '%s'.", path)

    def remove_directory(self, path, recursive=False):
        """Removes the directory pointed to by the given ``path``.

        If the second argument ``recursive`` is given a true value (see
        `Boolean arguments`), the directory is removed recursively. Otherwise
        removing fails if the directory is not empty.

        If the directory pointed to by the ``path`` does not exist, the keyword
        passes, but it fails, if the ``path`` points to a file.
        """
        path = self._absnorm(path)
        if not os.path.exists(path):
            self._link("Directory '%s' does not exist.", path)
        elif not os.path.isdir(path):
            self._error(f"Path '{path}' is not a directory.")
        else:
            if recursive:
                shutil.rmtree(path)
            else:
                self.directory_should_be_empty(
                    path, f"Directory '{path}' is not empty."
                )
                os.rmdir(path)
            self._link("Removed directory '%s'.", path)

    # Moving and copying files and directories

    def copy_file(self, source, destination) -> str:
        r"""Copies the source file into the destination.

        Source must be a path to an existing file or a glob pattern (see
        `Glob patterns`) that matches exactly one file. How the
        destination is interpreted is explained below.

        1) If the destination is an existing file, the source file is copied
        over it.

        2) If the destination is an existing directory, the source file is
        copied into it. A possible file with the same name as the source is
        overwritten.

        3) If the destination does not exist and it ends with a path
        separator (``/`` or ``\``), it is considered a directory. That
        directory is created and a source file copied into it.
        Possible missing intermediate directories are also created.

        4) If the destination does not exist and it does not end with a path
        separator, it is considered a file. If the path to the file does not
        exist, it is created.

        The resulting destination path is returned.

        See also `Copy Files`, `Move File`, and `Move Files`.
        """
        source, destination = self._prepare_copy_and_move_file(source, destination)
        if not self._are_source_and_destination_same_file(source, destination):
            source, destination = self._atomic_copy(source, destination)
            self._link("Copied file from '%s' to '%s'.", source, destination)
        return destination

    def _prepare_copy_and_move_file(self, source, destination):
        source = self._normalize_copy_and_move_source(source)
        destination = self._normalize_copy_and_move_destination(destination)
        if os.path.isdir(destination):
            destination = os.path.join(destination, os.path.basename(source))
        return source, destination

    def _normalize_copy_and_move_source(self, source):
        source = self._absnorm(source)
        sources = self._glob(source)
        if len(sources) > 1:
            self._error(f"Multiple matches with source pattern '{source}'.")
        if sources:
            source = sources[0]
        if not os.path.exists(source):
            self._error(f"Source file '{source}' does not exist.")
        if not os.path.isfile(source):
            self._error(f"Source file '{source}' is not a regular file.")
        return source

    def _normalize_copy_and_move_destination(self, destination):
        if isinstance(destination, pathlib.Path):
            destination = str(destination)
        is_dir = os.path.isdir(destination) or destination.endswith(("/", "\\"))
        destination = self._absnorm(destination)
        directory = destination if is_dir else os.path.dirname(destination)
        self._ensure_destination_directory_exists(directory)
        return destination

    def _ensure_destination_directory_exists(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
        elif not os.path.isdir(path):
            self._error(f"Destination '{path}' exists and is not a directory.")

    def _are_source_and_destination_same_file(self, source, destination):
        if self._force_normalize(source) == self._force_normalize(destination):
            self._link(
                "Source '%s' and destination '%s' point to the same file.",
                source,
                destination,
            )
            return True
        return False

    def _force_normalize(self, path):
        # TODO: Should normalize_path also support link normalization?
        # TODO: Should we handle dos paths like 'exampl~1.txt'?
        return os.path.realpath(normpath(path, case_normalize=True))

    def _atomic_copy(self, source, destination):
        """Copy file atomically (or at least try to).

        This method tries to ensure that a file copy operation will not fail
        if the destination file is removed during copy operation. The problem
        is that copying a file is typically not an atomic operation.

        Luckily moving files is atomic in almost every platform, assuming files
        are on the same filesystem, and we can use that as a workaround:
        - First move the source to a temporary directory that is ensured to
          be on the same filesystem as the destination.
        - Move the temporary file over the real destination.

        See also https://github.com/robotframework/robotframework/issues/1502
        """
        temp_directory = tempfile.mkdtemp(dir=os.path.dirname(destination))
        temp_file = os.path.join(temp_directory, os.path.basename(source))
        try:
            shutil.copy(source, temp_file)
            if os.path.exists(destination):
                os.remove(destination)
            shutil.move(temp_file, destination)
        finally:
            shutil.rmtree(temp_directory)
        return source, destination

    def move_file(self, source, destination) -> str:
        """Moves the source file into the destination.

        Arguments have exactly same semantics as with `Copy File` keyword.
        Destination file path is returned.

        If the source and destination are on the same filesystem, rename
        operation is used. Otherwise file is copied to the destination
        filesystem and then removed from the original filesystem.

        See also `Move Files`, `Copy File`, and `Copy Files`.
        """
        source, destination = self._prepare_copy_and_move_file(source, destination)
        if not self._are_source_and_destination_same_file(destination, source):
            shutil.move(source, destination)
            self._link("Moved file from '%s' to '%s'.", source, destination)
        return destination

    def copy_files(self, *sources_and_destination):
        """Copies specified files to the target directory.

        Source files can be given as exact paths and as glob patterns (see
        `Glob patterns`). At least one source must be given, but it is
        not an error if it is a pattern that does not match anything.

        Last argument must be the destination directory. If the destination
        does not exist, it will be created.

        Examples:
        | Copy Files | ${dir}/file1.txt  | ${dir}/file2.txt | ${dir2} |
        | Copy Files | ${dir}/file-*.txt | ${dir2}          |         |

        See also `Copy File`, `Move File`, and `Move Files`.
        """
        sources, dest = self._prepare_copy_and_move_files(sources_and_destination)
        for source in sources:
            self.copy_file(source, dest)

    def _prepare_copy_and_move_files(self, items):
        if len(items) < 2:
            self._error("Must contain destination and at least one source.")
        sources = self._glob_files(items[:-1])
        destination = self._absnorm(items[-1])
        self._ensure_destination_directory_exists(destination)
        return sources, destination

    def _glob_files(self, patterns):
        files = []
        for pattern in patterns:
            files.extend(self._glob(self._absnorm(pattern)))
        return files

    def move_files(self, *sources_and_destination):
        """Moves specified files to the target directory.

        Arguments have exactly same semantics as with `Copy Files` keyword.

        See also `Move File`, `Copy File`, and `Copy Files`.
        """
        sources, dest = self._prepare_copy_and_move_files(sources_and_destination)
        for source in sources:
            self.move_file(source, dest)

    def copy_directory(self, source, destination):
        """Copies the source directory into the destination.

        If the destination exists, the source is copied under it. Otherwise
        the destination directory and the possible missing intermediate
        directories are created.
        """
        source, destination = self._prepare_copy_and_move_directory(source, destination)
        shutil.copytree(source, destination)
        self._link("Copied directory from '%s' to '%s'.", source, destination)

    def _prepare_copy_and_move_directory(self, source, destination) -> tuple[str, str]:
        source = self._absnorm(source)
        destination = self._absnorm(destination)
        if not os.path.exists(source):
            self._error(f"Source '{source}' does not exist.")
        if not os.path.isdir(source):
            self._error(f"Source '{source}' is not a directory.")
        if os.path.exists(destination) and not os.path.isdir(destination):
            self._error(f"Destination '{destination}' is not a directory.")
        if os.path.exists(destination):
            base = os.path.basename(source)
            destination = os.path.join(destination, base)
        else:
            parent = os.path.dirname(destination)
            if not os.path.exists(parent):
                os.makedirs(parent)
        return source, destination

    def move_directory(self, source, destination):
        """Moves the source directory into a destination.

        Uses `Copy Directory` keyword internally, and ``source`` and
        ``destination`` arguments have exactly same semantics as with
        that keyword.
        """
        source, destination = self._prepare_copy_and_move_directory(source, destination)
        shutil.move(source, destination)
        self._link("Moved directory from '%s' to '%s'.", source, destination)

    # Environment Variables

    @keyword(types=None)
    def get_environment_variable(self, name, default=None) -> str:
        """Returns the value of an environment variable with the given name.

        If no environment variable is found, returns possible default value.
        If no default value is given, the keyword fails.

        Returned variables are automatically decoded to Unicode using
        the system encoding.

        Note that you can also access environment variables directly using
        the variable syntax ``%{ENV_VAR_NAME}``.
        """
        value = get_env_var(name, default)
        if value is None:
            self._error(f"Environment variable '{name}' does not exist.")
        return value

    def set_environment_variable(self, name, value):
        """Sets an environment variable to a specified value.

        Values are converted to strings automatically. Set variables are
        automatically encoded using the system encoding.
        """
        set_env_var(name, value)
        self._info(f"Environment variable '{name}' set to value '{value}'.")

    def append_to_environment_variable(self, name, *values, separator=os.pathsep):
        """Appends given ``values`` to environment variable ``name``.

        If the environment variable already exists, values are added after it,
        and otherwise a new environment variable is created.

        Values are, by default, joined together using the operating system
        path separator (``;`` on Windows, ``:`` elsewhere). This can be changed
        by giving a separator after the values like ``separator=value``.

        Examples (assuming ``NAME`` and ``NAME2`` do not exist initially):
        | Append To Environment Variable | NAME     | first  |       |
        | Should Be Equal                | %{NAME}  | first  |       |
        | Append To Environment Variable | NAME     | second | third |
        | Should Be Equal                | %{NAME}  | first${:}second${:}third |
        | Append To Environment Variable | NAME2    | first  | separator=-     |
        | Should Be Equal                | %{NAME2} | first  |                 |
        | Append To Environment Variable | NAME2    | second | separator=-     |
        | Should Be Equal                | %{NAME2} | first-second             |
        """
        sentinel = object()
        initial = self.get_environment_variable(name, sentinel)
        if initial is not sentinel:
            values = (initial, *values)
        self.set_environment_variable(name, separator.join(values))

    def remove_environment_variable(self, *names):
        """Deletes the specified environment variable.

        Does nothing if the environment variable is not set.

        It is possible to remove multiple variables by passing them to this
        keyword as separate arguments.
        """
        for name in names:
            value = del_env_var(name)
            if value:
                self._info(f"Environment variable '{name}' deleted.")
            else:
                self._info(f"Environment variable '{name}' does not exist.")

    def environment_variable_should_be_set(self, name, msg=None):
        """Fails if the specified environment variable is not set.

        The default error message can be overridden with the ``msg`` argument.
        """
        value = get_env_var(name)
        if not value:
            self._fail(msg, f"Environment variable '{name}' is not set.")
        self._info(f"Environment variable '{name}' is set to '{value}'.")

    def environment_variable_should_not_be_set(self, name, msg=None):
        """Fails if the specified environment variable is set.

        The default error message can be overridden with the ``msg`` argument.
        """
        value = get_env_var(name)
        if value:
            self._fail(msg, f"Environment variable '{name}' is set to '{value}'.")
        self._info(f"Environment variable '{name}' is not set.")

    def get_environment_variables(self) -> dict[str, str]:
        """Returns currently available environment variables as a dictionary.

        Both keys and values are decoded to Unicode using the system encoding.
        Altering the returned dictionary has no effect on the actual environment
        variables.
        """
        return get_env_vars()

    def log_environment_variables(self, level="INFO") -> dict[str, str]:
        """Logs all environment variables using the given log level.

        Environment variables are also returned the same way as with
        `Get Environment Variables` keyword.
        """
        variables = get_env_vars()
        for name in sorted(variables, key=lambda item: item.lower()):
            self._log(f"{name} = {variables[name]}", level)
        return variables

    # Path

    def join_path(self, base, *parts) -> str:
        """Joins the given path part(s) to the given base path.

        The path separator (``/`` or ``\\``) is inserted when needed and
        the possible absolute paths handled as expected. The resulted
        path is also normalized.

        Examples:
        | ${path} = | Join Path | my        | path  |
        | ${p2} =   | Join Path | my/       | path/ |
        | ${p3} =   | Join Path | my        | path  | my | file.txt |
        | ${p4} =   | Join Path | my        | /path |
        | ${p5} =   | Join Path | /my/path/ | ..    | path2 |
        =>
        - ${path} = 'my/path'
        - ${p2} = 'my/path'
        - ${p3} = 'my/path/my/file.txt'
        - ${p4} = '/path'
        - ${p5} = '/my/path2'
        """
        # FIXME: Is normalizing parts needed anymore?
        parts = [
            str(p) if isinstance(p, pathlib.Path) else p.replace("/", os.sep)
            for p in (base, *parts)
        ]
        return self.normalize_path(os.path.join(*parts))

    def join_paths(self, base, *paths) -> list[str]:
        """Joins given paths with base and returns resulted paths.

        See `Join Path` for more information.

        Examples:
        | @{p1} = | Join Paths | base     | example       | other |          |
        | @{p2} = | Join Paths | /my/base | /example      | other |          |
        | @{p3} = | Join Paths | my/base  | example/path/ | other | one/more |
        =>
        - @{p1} = ['base/example', 'base/other']
        - @{p2} = ['/example', '/my/base/other']
        - @{p3} = ['my/base/example/path', 'my/base/other', 'my/base/one/more']
        """
        return [self.join_path(base, path) for path in paths]

    def normalize_path(self, path, case_normalize=False) -> str:
        """Normalizes the given path.

        - Collapses redundant separators and up-level references.
        - Converts ``/`` to ``\\`` on Windows.
        - Replaces initial ``~`` or ``~user`` by that user's home directory.
        - If ``case_normalize`` is given a true value (see `Boolean arguments`)
          on Windows, converts the path to all lowercase.
        - Converts ``pathlib.Path`` instances to ``str``.

        Examples:
        | ${path1} = | Normalize Path | abc/           |
        | ${path2} = | Normalize Path | abc/../def     |
        | ${path3} = | Normalize Path | abc/./def//ghi |
        | ${path4} = | Normalize Path | ~robot/stuff   |
        =>
        - ${path1} = 'abc'
        - ${path2} = 'def'
        - ${path3} = 'abc/def/ghi'
        - ${path4} = '/home/robot/stuff'

        On Windows result would use ``\\`` instead of ``/`` and home directory
        would be different.
        """
        if isinstance(path, pathlib.Path):
            path = str(path)
        else:
            path = path.replace("/", os.sep)
        path = os.path.normpath(os.path.expanduser(path))
        # os.path.normcase doesn't normalize on OSX which also, by default,
        # has case-insensitive file system. Our robot.utils.normpath would
        # do that, but it's not certain would that, or other things that the
        # utility do, desirable.
        if case_normalize:
            path = os.path.normcase(path)
        return path or "."

    def split_path(self, path) -> tuple[str, str]:
        """Splits the given path from the last path separator (``/`` or ``\\``).

        The given path is first normalized (e.g. a possible trailing
        path separator is removed, special directories ``..`` and ``.``
        removed). The parts that are split are returned as separate
        components.

        Examples:
        | ${path1} | ${dir} =  | Split Path | abc/def         |
        | ${path2} | ${file} = | Split Path | abc/def/ghi.txt |
        | ${path3} | ${d2}  =  | Split Path | abc/../def/ghi/ |
        =>
        - ${path1} = 'abc' & ${dir} = 'def'
        - ${path2} = 'abc/def' & ${file} = 'ghi.txt'
        - ${path3} = 'def' & ${d2} = 'ghi'
        """
        return os.path.split(self.normalize_path(path))

    def split_extension(self, path) -> tuple[str, str]:
        """Splits the extension from the given path.

        The given path is first normalized (e.g. possible trailing
        path separators removed, special directories ``..`` and ``.``
        removed). The base path and extension are returned as separate
        components so that the dot used as an extension separator is
        removed. If the path contains no extension, an empty string is
        returned for it. Possible leading and trailing dots in the file
        name are never considered to be extension separators.

        Examples:
        | ${path} | ${ext} = | Split Extension | file.extension    |
        | ${p2}   | ${e2} =  | Split Extension | path/file.ext     |
        | ${p3}   | ${e3} =  | Split Extension | path/file         |
        | ${p4}   | ${e4} =  | Split Extension | p1/../p2/file.ext |
        | ${p5}   | ${e5} =  | Split Extension | path/.file.ext    |
        | ${p6}   | ${e6} =  | Split Extension | path/.file        |
        =>
        - ${path} = 'file' & ${ext} = 'extension'
        - ${p2} = 'path/file' & ${e2} = 'ext'
        - ${p3} = 'path/file' & ${e3} = ''
        - ${p4} = 'p2/file' & ${e4} = 'ext'
        - ${p5} = 'path/.file' & ${e5} = 'ext'
        - ${p6} = 'path/.file' & ${e6} = ''
        """
        path = self.normalize_path(path)
        basename = os.path.basename(path)
        if basename.startswith("." * basename.count(".")):
            return path, ""
        if path.endswith("."):
            path2 = path.rstrip(".")
            trailing_dots = "." * (len(path) - len(path2))
            path = path2
        else:
            trailing_dots = ""
        basepath, extension = os.path.splitext(path)
        if extension.startswith("."):
            extension = extension[1:]
        if extension:
            extension += trailing_dots
        else:
            basepath += trailing_dots
        return basepath, extension

    # Misc

    def get_modified_time(self, path, format="timestamp") -> int | str | list:
        """Returns the last modification time of a file or directory.

        How time is returned is determined based on the given ``format``
        string as follows. Note that all checks are case-insensitive.
        Returned time is also automatically logged.

        1) If ``format`` contains the word ``epoch``, the time is returned
           in seconds after the UNIX epoch. The return value is always
           an integer.

        2) If ``format`` contains any of the words ``year``, ``month``,
           ``day``, ``hour``, ``min`` or ``sec``, only the selected parts are
           returned. The order of the returned parts is always the one
           in the previous sentence and the order of the words in
           ``format`` is not significant. The parts are returned as
           zero-padded strings (e.g. May -> ``05``).

        3) Otherwise, and by default, the time is returned as a
           timestamp string in the format ``2006-02-24 15:08:31``.

        Examples (when the modified time of ``${CURDIR}`` is
        2006-03-29 15:06:21):
        | ${time} = | Get Modified Time | ${CURDIR} |
        | ${secs} = | Get Modified Time | ${CURDIR} | epoch |
        | ${year} = | Get Modified Time | ${CURDIR} | return year |
        | ${y} | ${d} = | Get Modified Time | ${CURDIR} | year,day |
        | @{time} = | Get Modified Time | ${CURDIR} | year,month,day,hour,min,sec |
        =>
        - ${time} = '2006-03-29 15:06:21'
        - ${secs} = 1143637581
        - ${year} = '2006'
        - ${y} = '2006' & ${d} = '29'
        - @{time} = ['2006', '03', '29', '15', '06', '21']
        """
        path = self._absnorm(path)
        if not os.path.exists(path):
            self._error(f"Path '{path}' does not exist.")
        mtime = get_time(format, os.stat(path).st_mtime)
        self._link(f"Last modified time of '%s' is {mtime}.", path)
        return mtime

    def set_modified_time(self, path, mtime):
        """Sets the file modification and access times.

        Changes the modification and access times of the given file to
        the value determined by ``mtime``. The time can be given in
        different formats described below. Note that all checks
        involving strings are case-insensitive. Modified time can only
        be set to regular files.

        1) If ``mtime`` is a number, or a string that can be converted
           to a number, it is interpreted as seconds since the UNIX
           epoch (1970-01-01 00:00:00 UTC). This documentation was
           originally written about 1177654467 seconds after the epoch.

        2) If ``mtime`` is a timestamp, that time will be used. Valid
           timestamp formats are ``YYYY-MM-DD hh:mm:ss`` and
           ``YYYYMMDD hhmmss``.

        3) If ``mtime`` is equal to ``NOW``, the current local time is used.

        4) If ``mtime`` is equal to ``UTC``, the current time in
           [http://en.wikipedia.org/wiki/Coordinated_Universal_Time|UTC]
           is used.

        5) If ``mtime`` is in the format like ``NOW - 1 day`` or ``UTC + 1
           hour 30 min``, the current local/UTC time plus/minus the time
           specified with the time string is used. The time string format
           is described in an appendix of Robot Framework User Guide.

        Examples:
        | Set Modified Time | /path/file | 1177654467         | # Time given as epoch seconds |
        | Set Modified Time | /path/file | 2007-04-27 9:14:27 | # Time given as a timestamp   |
        | Set Modified Time | /path/file | NOW                | # The local time of execution |
        | Set Modified Time | /path/file | NOW - 1 day        | # 1 day subtracted from the local time |
        | Set Modified Time | /path/file | UTC + 1h 2min 3s   | # 1h 2min 3s added to the UTC time |
        """
        mtime = parse_time(mtime)
        path = self._absnorm(path)
        if not os.path.exists(path):
            self._error(f"File '{path}' does not exist.")
        if not os.path.isfile(path):
            self._error(f"Path '{path}' is not a regular file.")
        os.utime(path, (mtime, mtime))
        time.sleep(0.1)  # Give OS some time to really set these times.
        tstamp = datetime.fromtimestamp(mtime).isoformat(" ", timespec="seconds")
        self._link(f"Set modified time of '%s' to {tstamp}.", path)

    def get_file_size(self, path) -> int:
        """Returns and logs file size as an integer in bytes."""
        path = self._absnorm(path)
        if not os.path.isfile(path):
            self._error(f"File '{path}' does not exist.")
        size = os.stat(path).st_size
        self._link(f"Size of file '%s' is {size} byte{s(size)}.", path)
        return size

    def list_directory(self, path, pattern=None, absolute=False) -> list[str]:
        """Returns and logs items in a directory, optionally filtered with ``pattern``.

        File and directory names are returned in case-sensitive alphabetical
        order, e.g. ``['A Name', 'Second', 'a lower case name', 'one more']``.
        Implicit directories ``.`` and ``..`` are not returned. The returned
        items are automatically logged.

        File and directory names are returned relative to the given path
        (e.g. ``'file.txt'``) by default. If you want them be returned in
        absolute format (e.g. ``'/home/robot/file.txt'``), give the ``absolute``
        argument a true value (see `Boolean arguments`).

        If ``pattern`` is given, only items matching it are returned. The pattern
        is considered to be a _glob pattern_ and the full syntax is explained in
        the `Glob patterns` section. With this keyword matching is always
        case-sensitive.

        Examples (using also other `List Directory` variants):
        | @{items} = | List Directory           | ${TEMPDIR} |
        | @{files} = | List Files In Directory  | /tmp | *.txt | absolute |
        | ${count} = | Count Files In Directory | ${CURDIR} | ??? |
        """
        items = self._list_dir(path, pattern, absolute)
        self._info(f"{len(items)} item{s(items)}:\n" + "\n".join(items))
        return items

    def list_files_in_directory(self, path, pattern=None, absolute=False) -> list[str]:
        """Wrapper for `List Directory` that returns only files."""
        files = self._list_files_in_dir(path, pattern, absolute)
        self._info(f"{len(files)} file{s(files)}:\n" + "\n".join(files))
        return files

    def list_directories_in_directory(
        self, path, pattern=None, absolute=False
    ) -> list[str]:
        """Wrapper for `List Directory` that returns only directories."""
        dirs = self._list_dirs_in_dir(path, pattern, absolute)
        label = "directory" if len(dirs) == 1 else "directories"
        self._info(f"{len(dirs)} {label}:\n" + "\n".join(dirs))
        return dirs

    def count_items_in_directory(self, path, pattern=None) -> int:
        """Returns and logs the number of all items in the given directory.

        The argument ``pattern`` has the same semantics as with `List Directory`
        keyword. The count is returned as an integer, so it must be checked e.g.
        with the built-in keyword `Should Be Equal As Integers`.
        """
        count = len(self._list_dir(path, pattern))
        self._info(f"{count} item{s(count)}.")
        return count

    def count_files_in_directory(self, path, pattern=None) -> int:
        """Wrapper for `Count Items In Directory` returning only file count."""
        count = len(self._list_files_in_dir(path, pattern))
        self._info(f"{count} file{s(count)}.")
        return count

    def count_directories_in_directory(self, path, pattern=None) -> int:
        """Wrapper for `Count Items In Directory` returning only directory count."""
        count = len(self._list_dirs_in_dir(path, pattern))
        label = "directory" if count == 1 else "directories"
        self._info(f"{count} {label}.")
        return count

    def _list_dir(self, path, pattern=None, absolute=False):
        path = self._absnorm(path)
        self._link("Listing contents of directory '%s'.", path)
        if not os.path.isdir(path):
            self._error(f"Directory '{path}' does not exist.")
        # result is already unicode but safe_str also handles NFC normalization
        items = sorted(safe_str(item) for item in os.listdir(path))
        if pattern:
            items = [i for i in items if fnmatch.fnmatchcase(i, pattern)]
        if absolute:
            path = os.path.normpath(path)
            items = [os.path.join(path, item) for item in items]
        return items

    def _list_files_in_dir(self, path, pattern=None, absolute=False):
        return [
            item
            for item in self._list_dir(path, pattern, absolute)
            if os.path.isfile(os.path.join(path, item))
        ]

    def _list_dirs_in_dir(self, path, pattern=None, absolute=False):
        return [
            item
            for item in self._list_dir(path, pattern, absolute)
            if os.path.isdir(os.path.join(path, item))
        ]

    def touch(self, path):
        """Emulates the UNIX touch command.

        Creates a file, if it does not exist. Otherwise changes its access and
        modification times to the current time.

        Fails if used with the directories or the parent directory of the given
        file does not exist.
        """
        path = self._absnorm(path)
        if os.path.isdir(path):
            self._error(f"Cannot touch '{path}' because it is a directory.")
        if not os.path.exists(os.path.dirname(path)):
            self._error(
                f"Cannot touch '{path}' because its parent directory does not exist."
            )
        if os.path.exists(path):
            mtime = round(time.time())
            os.utime(path, (mtime, mtime))
            self._link("Touched existing file '%s'.", path)
        else:
            open(path, "w", encoding="ASCII").close()
            self._link("Touched new file '%s'.", path)

    def _absnorm(self, path):
        return abspath(self.normalize_path(path))

    def _fail(self, *messages):
        raise AssertionError(next(msg for msg in messages if msg))

    def _error(self, msg):
        raise RuntimeError(msg)

    def _info(self, msg):
        self._log(msg, "INFO")

    def _link(self, msg, *paths):
        paths = tuple(f'<a href="file://{p}">{p}</a>' for p in paths)
        self._log(msg % paths, "HTML")

    def _warn(self, msg):
        self._log(msg, "WARN")

    def _log(self, msg, level):
        logger.write(msg, level)


class _Process:

    def __init__(self, command):
        self._command = self._process_command(command)
        self._process = os.popen(self._command)

    def __str__(self):
        return self._command

    def read(self):
        return self._process_output(self._process.read())

    def close(self):
        try:
            rc = self._process.close()
        except IOError:  # Has occurred sometimes in Windows
            return 255
        if rc is None:
            return 0
        # In Windows return code is value returned by
        # command (can be almost anything)
        # In other OS:
        #   Return code must be converted with 'rc >> 8' and it is
        #   between 0-255 after conversion
        if WINDOWS:
            return rc % 256
        return rc >> 8

    def _process_command(self, command):
        if ">" not in command:
            if command.endswith("&"):
                command = command[:-1] + " 2>&1 &"
            else:
                command += " 2>&1"
        return command

    def _process_output(self, output):
        if "\r\n" in output:
            output = output.replace("\r\n", "\n")
        if output.endswith("\n"):
            output = output[:-1]
        return console_decode(output)
