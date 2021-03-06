######################################################################
######################################################################
#  Copyright Tsung-Hsien Wen, Cambridge Dialogue Systems Group, 2016 #
######################################################################
######################################################################
from __future__ import print_function

import json

from future.utils import iteritems

file = open


class DialogActParser(object):
    """
    Parser for BAGEL-style Dialogue Acts.

    Assumes:
    1. dialogue acts are separated by the "|" token;
    2. slot value pairs are separated by the ";" token;
    3. special values specified in "resource/special_values.tx"
       unify the special values by dictionary keys;
    4. it strips all "'" or '"' token; and
    5. output json format
    """
    def __init__(self):
        fin = file('resource/special_values.txt')
        self.special_values = json.load(fin)
        fin.close()

    def parse(self, dact, keep_values=False):
        act_type = dact.split('(')[0]
        slt2vals = dact.split('(')[1].replace(')', '').split(';')
        jsact = {'acttype': act_type, 's2v': []}
        for slt2val in slt2vals:
            if slt2val == '':  # no slot
                jsact['s2v'].append((None, None))
            elif '=' not in slt2val:  # no value
                slt2val = slt2val.replace('_', '').replace(' ', '')
                jsact['s2v'].append((slt2val.strip('\'\"'), '?'))
            else:  # both slot and value exist
                s, v = [x.strip('\'\"') for x in slt2val.split('=')]
                s = s.replace('_', '').replace(' ', '')
                for key, vals in iteritems(self.special_values):
                    if v in vals:  # unify the special values
                        v = key
                if not v in self.special_values and \
                        not keep_values:  # delexicalisation
                    v = '_'
                jsact['s2v'].append((s, v))
        return jsact


class DActFormatter(object):
    """
    Basic Dialogue Act formatter.

    This is the abstract class for Hard and Soft subclasses.
    It defines the basic parser command.
    """
    def __init__(self):
        self.parser = DialogActParser()
        self.special_values = self.parser.special_values.keys()

    def format(self, dact, keep_values=False):
        raise NotImplementedError('method format() hasn\'t been implemented')

    def parse(self, dact, keep_values=False):
        return self.parser.parse(dact, keep_values)


class SoftDActFormatter(DActFormatter):
    """
    Soft Dialogue Act formatter.

    Subclasses DActFormatter and provides main interface for parser/formatter.

    Formatting the JSON DAct produced by DialogActParser
       into a feature format fed into the network.
    """
    def __init__(self):
        DActFormatter.__init__(self)

    def format(self, dact):
        jsact = super(SoftDActFormatter, self).parse(dact)
        mem = {}
        feature = []
        for sv in jsact['s2v']:
            s, v = sv
            if s is None:  # no slot no value
                continue  # skip it
            elif v == '?':  # question case
                feature.append((s, v))
            elif v == '_':  # categories
                if s in mem:  # multiple feature values
                    feature.append((s, v + str(mem[s])))
                    mem[s] += 1
                else:  # first occurrence
                    feature.append((s, v + '1'))
                    mem[s] = 2
            elif v in self.special_values:  # special values
                feature.append((s, v))
        feature = [('a', jsact['acttype'])] + sorted(feature)
        return feature

    def parse(self, dact, keep_values=False):
        return self.parser.parse(dact, keep_values)


class HardDActFormatter(DActFormatter):
    """
    Hard Dialogue Act formatter.

    Subclasses DActFormatter and provides main interface for parser/formatter.

    Formatting the JSON DAct produced by DialogActParser
       into a feature format fed into the network.
    Output format example:
       ['A-inform', 'SV-count=VALUE', 'SV-type=VALUE']
       i.e. the format used in EMNLP 2015 submission
    """
    def __init__(self):
        DActFormatter.__init__(self)

    def format(self, dact):
        jsacts = super(HardDActFormatter, self).parse(dact)
        features = []
        mem = {}
        for jsact in jsacts:
            feature = []
            for sv in jsact['s2v']:
                s, v = sv
                if s is None:  # no slot no value
                    feature.append('SV-NoSlot=NoValue')
                elif v == '?':  # question case
                    feature.append('SV-' + s + '=PENDING')
                elif v == '_':  # categories
                    if s in mem:  # multiple feature values
                        feature.append('SV-' + s + '=VALUE' + str(mem[s]))
                        mem[s] += 1
                    else:  # first occurance
                        feature.append('SV-' + s + '=VALUE')
                        mem[s] = 1
                elif v in self.special_values:  # special values
                    feature.append('SV-' + s + '=' + v)
            features.append(['A-' + jsact['acttype']] + sorted(feature))
        return features

    def parse(self, dact, keep_values=False):
        return self.parser.parse(dact, keep_values)


if __name__ == '__main__':
    # dadp = DialogActDelexicalizedParser()
    dadp = HardDActFormatter()

    print(dadp.format("inform(type='restaurant';count='182';area=dont_care)"))
    print(dadp.format("reqmore()"))
    print(dadp.format("request(area)"))
    print(dadp.format("inform(name='fifth floor';address='hotel palomar 12 fourth street or rosie street')"))
    print(dadp.format("inform(name='fifth floor';address='hotel palomar 12 fourth street and rosie street')"))
    print(dadp.format("?select(food=dont_care;food='sea food')"))
    print(dadp.format("?select(food='yes';food='no')"))
    print(dadp.format("?select(battery rating=exceptional;battery rating=standard)"))
    print(dadp.format("suggest(weight range=heavy;weight range=light weight;weightrange=dontcare)"))
    print(dadp.format(
        "?compare(name=satellite morpheus 36;warranty=1 year european;dimension=33.7 inch;name=tecra proteus 23;warranty=1 year international;dimension=27.4 inch)"))
