######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2016 #
######################################################################
######################################################################
import re

file = open

fin = file('utils/nlp/mapping.pair')
REPLACEMENTS = []
for line in fin.readlines():
    tok_from, tok_to = line.replace('\n', '').split('\t')
    REPLACEMENTS.append((' ' + tok_from + ' ', ' ' + tok_to + ' '))


def insert_space(token: str, text: str) -> str:
    """
    Add preceding and following space around `token` in `text`.

    Does not insert spaces if spaces are already present or the token occurs surrounded by digits.
    """
    start_index = 0
    while True:
        start_index = text.find(token, start_index)
        if start_index == -1:
            break
        # this is because insertSpace() is called with characters which can be used in numerals to delimit segments
        # i.e. token could be a comma or a period
        if (start_index + 1 < len(text) and
                re.match('[0-9]', text[start_index - 1]) and
                re.match('[0-9]', text[start_index + 1])):
            start_index += 1
            continue
        # add a space before the token if the preceding char is not already a space
        # TODO DMH: this fails when start_index == 0, right?
        if text[start_index - 1] != ' ':
            text = text[:start_index] + ' ' + text[start_index:]
            start_index += 1
        # add a space following the token if we're not at the end of the text and already have a space following
        if start_index + len(token) < len(text) and text[start_index + len(token)] != ' ':
            text = text[:start_index + 1] + ' ' + text[start_index + 1:]
        start_index += 1
    return text


def normalize(text):
    # lower case every word
    text = text.lower()

    # replace white spaces in front and end
    text = re.sub(r'^\s*|\s*$', '', text)

    # normalize phone number
    ms = re.findall('\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})', text)
    if ms:
        sidx = 0
        for m in ms:
            sidx = text.find(m[0], sidx)
            if text[sidx - 1] == '(':
                sidx -= 1
            eidx = text.find(m[-1], sidx) + len(m[-1])
            text = text.replace(text[sidx:eidx], ''.join(m))

    # replace st.
    text = text.replace(';', ',')
    text = re.sub('$\/', '', text)
    text = text.replace('/', ' and ')

    # replace other special characters
    text = re.sub('[\":<>@]', '', text)
    # text = re.sub('[\":\<>@\(\)]','',text)
    text = text.replace(' - ', '')

    # insert white space before and after tokens:
    for token in ['?', '.', ',', '!']:
        text = insert_space(token, text)

    # remove all text or word initial/final apostrophes
    text = re.sub('^\'', '', text)
    text = re.sub('\'$', '', text)
    text = re.sub('\'\s', ' ', text)
    text = re.sub('\s\'', ' ', text)
    # replace it's, does't, you'd ... etc
    for fromx, tox in REPLACEMENTS:
        text = ' ' + text + ' '
        text = text.replace(fromx, tox)[1:-1]

    # insert white space for 's
    text = insert_space('\'s', text)

    # collapse multiple spaces to a single space
    text = re.sub(' +', ' ', text)

    # concatenate numbers
    tokens = text.split()
    i = 1
    while i < len(tokens):
        if re.match(u'^\d+$', tokens[i]) and re.match(u'\d+$', tokens[i - 1]):
            tokens[i - 1] += tokens[i]
            del tokens[i]
        else:
            i += 1
    text = ' '.join(tokens)

    return text
