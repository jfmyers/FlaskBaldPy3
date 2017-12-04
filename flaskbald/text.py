import re
import unicodedata
import phonenumbers


try:
    type(unicode)
except NameError:
    def unicode(txt, errors=None):
        return txt.decode('utf-8')

# first pass, anything before a CAPLower gets separated. i.e. CAP_Lower
#  123Lower -> 123_Lower
first_pass = re.compile(r'(.)([A-Z][a-z]+)')
# second pass, anything lowerCAP gets split then lowercased lower_cap
second_pass = re.compile(r'([a-z0-9])([A-Z])')


# technically this is PascalCase (or StudlyCaps)
def camel_to_underscore(text):
    '''Convert CamelCase text into underscore_separated text.'''
    return second_pass.sub(r'\1_\2', first_pass.sub(r'\1_\2', text)).lower()


def underscore_to_camel(text):
    '''Convert underscore_separated text into CamelCase text.'''
    return ''.join([token.capitalize() for token in text.split(r'_')])


ordinal_suffixes = {1: 'st', 2: 'nd', 3: 'rd'}


def ordinal_suffix(num):
    '''Returns the ordinal suffix of an interger (1st, 2nd, 3rd).'''
    if 10 <= abs(num) % 100 <= 20:
        return 'th'
    return ordinal_suffixes.get(abs(num) % 10, 'th')


plural_patterns = [(re.compile(pattern), re.compile(search), replace
                                        ) for pattern, search, replace in (
                         ('[^aeiouz]z$', '$', 's'),
                         ('[aeiou]z$', '$', 'zes'),
                         ('[sx]$', '$', 'es'),
                         ('[^aeioudgkprt]h$', '$', 'es'),
                         ('[^aeiou]y$', 'y$', 'ies'),
                         ('$', '$', 's'))]


def _build_plural_rule(input_pattern):
    pattern, search, replace = input_pattern
    return lambda word: pattern.search(word) and search.sub(replace, word)


plural_rules = list(map(_build_plural_rule, plural_patterns))


def pluralize(text):
    '''
    Returns a pluralized from of the input text following simple naive
    english language pluralization rules.

    Smart enough to turn fox into foxes and quiz into quizzes. Does not catch
    all pluralization rules, however.
    '''
    for rule in plural_rules:
        result = rule(text)
        if result:
            return result


def strip_accents(text):
    '''
    Strip diacriticals from characters. This will change the meaning of words
    but for places where unicode can't be used (or ASCII only) francais looks
    better than fran-ais or fran?ais.
    '''
    if isinstance(text, bytes):
        return unicode(text, errors='ignore')
    return ''.join((c for c in unicodedata.normalize('NFD', text) if
                                              unicodedata.category(c) != 'Mn'))


def split_full_name(full_name):
    if type(full_name) is not str and type(full_name) is not unicode:
        return None, None

    full_name = full_name.strip()

    names = full_name.split(' ')

    if len(names) > 2:
        first_name = names[0]
        first_name = first_name.strip()
        last_name = ' '.join(names[1:])
        last_name = last_name.strip()
    elif len(names) == 2:
        first_name, last_name = names
    else:
        first_name = full_name
        first_name = first_name.strip()
        last_name = None

    return first_name, last_name


def valid_phone_number(phone_number):
    try:
        parsed_phone_number = phonenumbers.parse(phone_number, None)
    except phonenumbers.phonenumberutil.NumberParseException:
        return False

    return phonenumbers.is_valid_number(parsed_phone_number)


def format_phone_number(phone_number):
    DEFAULT_COUNTRY_REGION = '+1'
    try:
        parsed_phone_number = phonenumbers.parse(phone_number, None)
    except phonenumbers.phonenumberutil.NumberParseException:
        phone_number = ''.join([DEFAULT_COUNTRY_REGION, phone_number])

    try:
        parsed_phone_number = phonenumbers.parse(phone_number, None)
    except phonenumbers.phonenumberutil.NumberParseException:
        return None

    if phonenumbers.is_valid_number(parsed_phone_number) is False:
        return None

    return phonenumbers.format_number(parsed_phone_number, phonenumbers.PhoneNumberFormat.E164)


def pretty_phone_number(phone_number):
    parsed_phone_number = phonenumbers.parse(phone_number, None)
    formatted_number = phonenumbers.format_number(parsed_phone_number, phonenumbers.PhoneNumberFormat.NATIONAL)
    split_number = formatted_number.split(" ")
    number = ''
    if len(split_number) == 3:
        return "({0}) {1}-{2}".format(split_number[0], split_number[1], split_number[3])
    else:
        return formatted_number


def are_similar(str1, *args):
    for str2 in args:
        score = Similarity(str1, str2).get_sim()
        if score > .70:
            return True

    return False


def similarity_score(list_of_text, input_text):
    scores = []
    for test_text in list_of_text:
        scores.append(Similarity(input_text, test_text).get_sim())
    return max(scores)


#Determine Character Pairs of a String and Return the Pairs in a List
# ex: United = ['un','ni', 'it', 'te', 'ed']
class CharPairs:
    def __init__(self, string):
        self.string = string.lower()
        self.create_char_list()
        self.create_char_pairs()

    def create_char_list(self):
        self.str_length = 0
        self.strChars = {}
        for char in self.string:
            self.strChars[self.str_length] = char
            self.str_length += 1

    def create_char_pairs(self):
        self.charPairs = []
        self.charPairCount = 0
        count = 0
        for char in self.strChars:
            if count < (self.str_length -1):
                y = count + 1
                pair = self.strChars[count] + self.strChars[y]
                self.charPairs.append(pair)
                self.charPairCount += 1

            count += 1

    def getCharPairs(self):
        return self.charPairs

    def getCharPairCount(self):
        return self.charPairCount


#Word Similarity Algorithm
#Similarity(string1, string2) = 2 * number of incommon char. pairs / sum of total number of char. pairs in each string
class Similarity:
    def __init__(self,string1, string2):
        #get character pairs for string1
        strChar1 = CharPairs(string1)
        self.charPair1 = strChar1.getCharPairs()
        self.charPair1Count = strChar1.getCharPairCount()
        self.string1 = string1.lower()
        #get character pairs for string2
        strChar2 = CharPairs(string2)
        self.charPair2 = strChar2.getCharPairs()
        self.charPair2Count = strChar2.getCharPairCount()
        self.string2 = string2.lower()
        #run steps
        self.find_in_common_char_pairs()
        self.calculate_similarity()

    def find_in_common_char_pairs(self):
        self.incommon = set(self.charPair1).intersection(self.charPair2)
        self.incommon_count = 0
        for i in self.incommon:
            self.incommon_count += 1

    def calculate_similarity(self):
        numerator = 2 * self.incommon_count
        denominator = self.charPair1Count + self.charPair2Count
        # getcontext().prec = 4
        self.sim = float(numerator) / float(denominator)

    def get_sim(self):
        return self.sim

email_re = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'  # quoted-string
    r')@(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,63}\.?$', re.IGNORECASE)


def valid_email(email):
    if not email or not email_re.match(email):
        return False
    return True


def display_name(first_name, last_name):
    if first_name and last_name:
        return ' '.join([first_name, last_name])
    elif first_name:
        return first_name
    elif last_name:
        return last_name
    else:
        return None
