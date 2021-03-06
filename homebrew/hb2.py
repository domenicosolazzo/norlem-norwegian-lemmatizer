import sys
import codecs
from argparse import ArgumentParser
from nltk.stem.snowball import SnowballStemmer

def lemmatize(main_model, backup_model, all_lemmas, pos, evaluation, test_file):

    # here we wnat to do something smart with hyphenated words,
    # for instancd splitting at the hyphen, lemmatize the last part and
    # then recontructing the lemma :)
    stemmer = SnowballStemmer("norwegian")

    token_index = 0
    pos_index = 1

    if evaluation:
        total = 0.0
        right = 0.0
        token_index = 1
        pos_index = 3
    
    test_lines = test_file.readlines()

    for i, line in enumerate(test_lines):
        if line != '\n':
            try:
                next_line = test_lines[i+1].split()
                next_token = "%s" % (next_line[token_index].lower())
            except:
                next_token = '\n'
            if evaluation:
                total += 1
            
            line = line.split()
            splitted_token = line[token_index].split("-")
            if '' not in splitted_token:
                token = splitted_token[-1]
            else:
                splitted_token = []
                token = line[token_index]
            stemmed = stemmer.stem(token)
            lemma = token
            
            if pos:
                key = "%s_%s" % (token, line[pos_index])
            else:
                key = "%s" % (token)
            key = key.lower()
            # found the token/pos
            if key in main_model:
                count = 0
                # found the context
                if next_token in main_model[key]:
                    for lem in main_model[key][next_token]:
                        # lemma is the most frequent lemma for the context
                        if main_model[key][next_token][lem] > count:
                            count = main_model[key][next_token][lem]
                            lemma = lem
                # did not find the context
                else:
                    for nt in main_model[key]:
                        for lem in main_model[key][nt]:
                            # lemma is the most frequent lemma for the token/pos
                            if main_model[key][nt][lem] > count:
                                count = main_model[key][nt][lem]
                                lemma = lem
            elif backup_model != 'token':
                if key.lower()  in backup_model:
                    lemma = backup_model[key.lower()]
                #elif stemmed in all_lemmas:
                else:
                    lemma = stemmed
            if len(splitted_token) > 1:
                token = '-'.join(splitted_token[:-1])
                lemma = '-'.join([token, lemma])

            if evaluation:
                if lemma.lower() == line[2].lower():
                    right +=1
                #else:
                #    print line[token_index].encode('utf8').lower(), lemma.encode('utf8').lower(), line[2].encode('utf8').lower()
            if not evaluation:
                print "%s\t%s" % (line[0].encode('utf8'), lemma.encode('utf8'))
        else:
            if not evaluation:
                print
    if evaluation:
        print right / total


# So how about embedding in a bigram context for each word?
# {key: {context1: {lemma: count, lemma: count} ... }} 
def train(ndt, ordbanken=False, pos=False):
    main_model = {}
    ndt_lines = ndt.readlines()
    for i, line in enumerate(ndt_lines):
        if line != '\n':
            line = line.split()
            try:
                next_line = ndt_lines[i+1].split()
            except:
                next_line = []
            next_token = "%s" % (next_line[1].lower()) if len(next_line) > 0 else '\n'
            if pos:
                key = "%s_%s" % (line[1], line[3])
            else:
                key = "%s" % (line[1])
            key = key.lower()
            lemma = line[2]
            if key not in main_model:
                main_model[key] = {}
            if next_token not in main_model[key]:
                main_model[key][next_token] = {}
            if lemma in main_model[key][next_token]:
                main_model[key][next_token][lemma] += 1
            else:
                main_model[key][next_token][lemma] = 1
    if ordbanken:
        backup_model = {}
        all_lemmas = []
        for line in ordbanken:
            if not line.startswith("*") and not line.startswith('\r\n'):
                line = line.split('\t')
                if pos:
                    key = "%s_%s" % (line[2], line[3].split()[0])
                else:
                    key = "%s" % (line[2])
                lemma = line[1]
                all_lemmas.append(lemma)
                backup_model[key] = lemma

        return (main_model, backup_model, set(all_lemmas))        
    else:
        return main_model

def levenshteinDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]

def main():
    argparser = ArgumentParser(description="Lemmatize Norwegian.")
    argparser.add_argument('--ndt', help="path to the NDT file used for training", required=True)
    argparser.add_argument('--ordbanken', help="path to the ordbanken file used for backup training")
    argparser.add_argument('--eval', help='accept an NDT formatted file as input and calculate accuracy', action="store_true")
    argparser.add_argument('--pos', help='use POS-disambiguated tokens', action="store_true")
    argparser.add_argument('input', help='the input to be lemmatized. Can be in the NDT format if run with --eval', nargs='+')   
    args = argparser.parse_args()

    ndt = codecs.open(args.ndt, 'r', 'utf8')
    if args.ordbanken:
        ordbanken = codecs.open(args.ordbanken, 'r', 'utf-8')
        main_model, backup_model, all_lemmas = train(ndt, ordbanken=ordbanken, pos=args.pos)
    else:
        main_model = train(ndt, pos=args.pos)
        backup_model = 'token'

    test = codecs.open(args.input[0], 'r', 'utf8')
    lemmatize(main_model, backup_model, all_lemmas, args.pos, args.eval, test)

if __name__ == '__main__':
    main()
