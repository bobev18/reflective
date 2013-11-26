def clear_bad_chars(text):
    # KILL BAD UNICODE
    BAD_CHARS = ['\u200b', '\u2122', '™', '\uf04a', '\u2019', '\u2013', '\u2018', '\xae', '\u201d',  ]
    BAD_CHARS = ['\u200b', '\u2122', '™', '\uf04a', '\u2019', '\u2013', '\u2018', '\xae', '\u201d', '©', '“' ]
    for bc in BAD_CHARS:
        text = text.replace(bc, '')
    # text = text.encode('utf-8','backslashreplace').decode('utf-8','surrogateescape') # failing
    # I think I need to have the encoding specified during the urllib2.read( ) === myweb3
    # REGULAR CLEANS
    text = text.replace('u003C', '<')
    text = text.replace('u003E', '>')
    return text
    # ok - tied the following and it errored on char: '\\u200b'
    # return smart_text(text, encoding='utf-8', strings_only=False, errors='strict')

    