FORMATS = [
    {
        "category": "Documents",
        "formats": [
            {"ext": "pdf", "label": "PDF"},
            {"ext": "doc", "label": "DOC"},
            {"ext": "docx", "label": "DOCX"},
            {"ext": "odt", "label": "ODT"},
            {"ext": "rtf", "label": "RTF"},
            {"ext": "txt", "label": "TXT"},
            {"ext": "md", "label": "Markdown"},
            {"ext": "html", "label": "HTML"},
        ],
    },
    {
        "category": "Images",
        "formats": [
            {"ext": "png", "label": "PNG"},
            {"ext": "jpg", "label": "JPG"},
            {"ext": "jpeg", "label": "JPEG"},
            {"ext": "gif", "label": "GIF"},
            {"ext": "bmp", "label": "BMP"},
            {"ext": "tiff", "label": "TIFF"},
            {"ext": "webp", "label": "WebP"},
            {"ext": "svg", "label": "SVG"},
        ],
    },
    {
        "category": "Audio",
        "formats": [
            {"ext": "mp3", "label": "MP3"},
            {"ext": "wav", "label": "WAV"},
            {"ext": "flac", "label": "FLAC"},
            {"ext": "ogg", "label": "OGG"},
            {"ext": "m4a", "label": "M4A"},
            {"ext": "aac", "label": "AAC"},
        ],
    },
    {
        "category": "Video",
        "formats": [
            {"ext": "mp4", "label": "MP4"},
            {"ext": "mov", "label": "MOV"},
            {"ext": "mkv", "label": "MKV"},
            {"ext": "avi", "label": "AVI"},
            {"ext": "webm", "label": "WebM"},
        ],
    },
    {
        "category": "Archives",
        "formats": [
            {"ext": "zip", "label": "ZIP"},
            {"ext": "tar", "label": "TAR"},
            {"ext": "tar.gz", "label": "TAR.GZ"},
        ],
    },
    {
        "category": "Ebooks",
        "formats": [
            {"ext": "epub", "label": "EPUB"},
            {"ext": "mobi", "label": "MOBI"},
            {"ext": "azw3", "label": "AZW3"},
        ],
    },
]

PIPELINES = [
    {
        "id": "imagemagick",
        "tool": "imagemagick",
        "inputs": ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp", "svg"],
        "outputs": ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "webp"],
        "description": "Image conversions via ImageMagick",
    },
    {
        "id": "ffmpeg-audio",
        "tool": "ffmpeg",
        "inputs": ["mp3", "wav", "flac", "ogg", "m4a", "aac"],
        "outputs": ["mp3", "wav", "flac", "ogg", "m4a", "aac"],
        "description": "Audio conversions via ffmpeg",
    },
    {
        "id": "ffmpeg-video",
        "tool": "ffmpeg",
        "inputs": ["mp4", "mov", "mkv", "avi", "webm"],
        "outputs": ["mp4", "mov", "mkv", "avi", "webm"],
        "description": "Video conversions via ffmpeg",
    },
    {
        "id": "libreoffice",
        "tool": "libreoffice",
        "inputs": ["doc", "docx", "odt", "rtf", "ppt", "pptx", "xls", "xlsx"],
        "outputs": ["pdf", "docx", "odt", "rtf", "txt", "html"],
        "description": "Office document conversions via LibreOffice",
    },
    {
        "id": "pandoc",
        "tool": "pandoc",
        "inputs": ["md", "txt", "rtf", "docx", "html"],
        "outputs": ["pdf", "docx", "html", "odt", "txt"],
        "description": "Document conversions via Pandoc",
    },
    {
        "id": "ebook-convert",
        "tool": "ebook-convert",
        "inputs": ["epub", "mobi", "azw3"],
        "outputs": ["epub", "mobi", "azw3"],
        "description": "Ebook conversions via Calibre ebook-convert",
    },
    {
        "id": "archive",
        "tool": "archive",
        "inputs": ["zip", "tar", "tar.gz"],
        "outputs": ["zip", "tar", "tar.gz"],
        "description": "Archive conversions via Python",
    },
]
