from .ue_format import UEFormatImport, UEModelOptions, Log
import zstandard as zstd
from . import ue_format

ue_format.zstd_decompresser = zstd.ZstdDecompressor()
Log.NoLog = True

def get_importer():
    return UEFormatImport(UEModelOptions(False))

def import_model(filepath):
    importer = get_importer()
    return importer.import_file(filepath)
