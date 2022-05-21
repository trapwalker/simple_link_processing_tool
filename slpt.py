#! /usr/bin/python3

import sys
import logging
from pathlib import Path


log = logging.getLogger(__name__)


class AbstractProcessFilesError(Exception):
    pass


class SkipLineError(AbstractProcessFilesError):
    pass


class WrongDestinationPath(AbstractProcessFilesError):
    pass


class CantCreateDestFolder(WrongDestinationPath):
    pass


class CantCreateDestFile(WrongDestinationPath):
    pass


class OutputFileAlreadyExists(AbstractProcessFilesError):
    pass


def log_setup(debug=True):
    logging.basicConfig(
        stream=sys.stderr,
        level='DEBUG' if debug else 'INFO',
        format='[%(levelname)-7s] %(message)s',
    )


def process_files(input_path=Path('.'), output_path=Path('result'), input_files_mask='*.txt', overwrite=True):
    if output_path.exists() and output_path.is_dir():
        log.info(f'Result folder {output_path!r} already exists.')
    elif output_path.exists():
        err = f"Result path is not directory: {output_path!r}"
        log.error(err)
        raise WrongDestinationPath(err)
    else:
        log.info(f'Result folder {output_path!r} does not exists. Try to create...')
        try:
            output_path.mkdir(exist_ok=True)
        except Exception as e:
            raise CantCreateDestFolder(f"Can't create result folder {output_path!r}")

    files = list(input_path.glob(input_files_mask))
    log.debug(f'Found {len(files)} input files by mask {input_files_mask!r}')
    for fn in files:
        try:
            process_one_file(fn, output_path=output_path, overwrite=overwrite)
        except AbstractProcessFilesError as e:
            log.error(f'Error while processing file {fn!r}. SKIP by {e}')
        except Exception as e:
            log.exception(f'Unexpected error while processing file {fn!r}. SKIP by {e}:')


def process_one_file(fn: Path, output_path: Path, overwrite=True):
    result_file_name = output_path / fn.name
    log.debug(f'Processing {fn!r} to {result_file_name!r}...')

    if result_file_name.exists():
        if not overwrite:
            raise OutputFileAlreadyExists(f'Output file {result_file_name!r} already exists. Remove them or turn ON overwrite mode.')
        if not result_file_name.is_file():
            raise CantCreateDestFile(f"Output path {result_file_name!r} existed and not a file. Can't overwrite them.")

    with fn.open() as stream_in, result_file_name.open('w') as stream_out:
        for line in stream_in:
            try:
                result = process_line(line)
                if result is not None:
                    stream_out.write(result)
            except (SkipLineError, AssertionError) as e:
                log.debug(f'Line {line!r} was skipped: {e}')
            except Exception as e:
                log.exception(f'Line {line!r} was skipped with unexpected error: {e}')


def process_line(line: str) -> str or None:
    """Здесь пишем обработчик одной единственной строки.
    Если строка ненужная, то возвращаем None, иначе делаем необходимые преобразования и возвращаем результат.
    Можно также пропустить строку бросив исключение SkipLineError или AssertionError
    """
    words = line.split('/')[4:6]
    assert words, 'Wrong line format'
    assert words[0] == 'channel', 'Channel links only supported'

    return '/'.join(words) + '\n'


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    debug = '--debug' in argv
    overwrite = '--no_overwrite' not in argv
    log_setup(debug=debug)
    try:
        process_files(overwrite=overwrite)
    except Exception as e:
        log.error(e)


if __name__ == '__main__':
    main()
