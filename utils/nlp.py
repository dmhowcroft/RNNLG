######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2016 #
######################################################################
######################################################################
import re
import regex

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
    ms = re.findall(r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})', text)
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
    text = re.sub(r'$\/', '', text)
    text = text.replace('/', ' and ')

    # replace other special characters
    text = re.sub(r'[\":<>@]', '', text)
    # text = re.sub(r'[\":\<>@\(\)]','',text)
    text = text.replace(' - ', '')

    # insert white space before and after tokens:
    for token in ['?', '.', ',', '!', ';', ':']:
        text = insert_space(token, text)

    # remove all text or word initial/final apostrophes
    text = re.sub(r'^\'', '', text)
    text = re.sub(r'\'$', '', text)
    text = re.sub(r'\'\s', ' ', text)
    text = re.sub(r'\s\'', ' ', text)
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
        if re.match(r'^\d+$', tokens[i]) and re.match(r'\d+$', tokens[i - 1]):
            tokens[i - 1] += tokens[i]
            del tokens[i]
        else:
            i += 1
    final_toks = []
    # print(tokens)

    for token in tokens:
        # print(re.search(r'\d[A-Za-z]', token))
        if re.search(r'[0-9$][A-Za-z]', token):
            # print(token)
            token = re.sub(r'([0-9$])([A_Za-z])', r'\1 \2', token)
            # print(token.split())
            final_toks += token.split()
        elif re.search(r'[A-Za-z][0-9$]', token):
            # print(token)
            token = re.sub(r'([A_Za-z])([0-9$])', r'\1 \2', token)
            # print(token.split())
            final_toks += token.split()
        else:
            final_toks.append(token)
    text = ' '.join(final_toks)

    return tgen_tokenize(text)


def tgen_tokenize(text):
    """Tokenize the given text (i.e., insert spaces around all tokens)"""
    toks = ' ' + text + ' '  # for easier regexes

    # enforce space around all punct
    toks = regex.sub(r'(([^\p{IsAlnum}\s\.\,−\-])\2*)', r' \1 ', toks)  # all punct (except ,-.)
    toks = regex.sub(r'([^\p{N}])([,.])([^\p{N}])', r'\1 \2 \3', toks)  # ,. & no numbers
    toks = regex.sub(r'([^\p{N}])([,.])([\p{N}])', r'\1 \2 \3', toks)  # ,. preceding numbers
    toks = regex.sub(r'([\p{N}])([,.])([^\p{N}])', r'\1 \2 \3', toks)  # ,. following numbers
    toks = regex.sub(r'(–-)([^\p{N}])', r'\1 \2', toks)  # -/– & no number following
    toks = regex.sub(r'(\p{N} *|[^ ])(-)', r'\1\2 ', toks)  # -/– & preceding number/no-space
    toks = regex.sub(r'([-−])', r' \1', toks)  # -/– : always space before

    # keep apostrophes together with words in most common contractions
    toks = regex.sub(r'([\'’´]) (s|m|d|ll|re|ve)\s', r' \1\2 ', toks)  # I 'm, I 've etc.
    toks = regex.sub(r'(n [\'’´]) (t\s)', r' \1\2 ', toks)  # do n't

    # other contractions, as implemented in Treex
    toks = regex.sub(r' ([Cc])annot\s', r' \1an not ', toks)
    toks = regex.sub(r' ([Dd]) \' ye\s', r' \1\' ye ', toks)
    toks = regex.sub(r' ([Gg])imme\s', r' \1im me ', toks)
    toks = regex.sub(r' ([Gg])onna\s', r' \1on na ', toks)
    toks = regex.sub(r' ([Gg])otta\s', r' \1ot ta ', toks)
    toks = regex.sub(r' ([Ll])emme\s', r' \1em me ', toks)
    toks = regex.sub(r' ([Mm])ore\'n\s', r' \1ore \'n ', toks)
    toks = regex.sub(r' \' ([Tt])is\s', r' \'\1 is ', toks)
    toks = regex.sub(r' \' ([Tt])was\s', r' \'\1 was ', toks)
    toks = regex.sub(r' ([Ww])anna\s', r' \1an na ', toks)

    # clean extra space
    toks = regex.sub(r'\s+', ' ', toks)
    toks = toks.strip()
    return toks