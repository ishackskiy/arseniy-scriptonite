from string import punctuation
from json import loads
import codecs
import re
from typing import NamedTuple, override
import csv

tags = ["(.)", "(:)", "(*)"]
punctuation = punctuation + "«»" + '"' + "”" + "“" + "“" + "”" + "—" + "–"


def load_usage(path: str):
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        return {get_csv_inf(row[2]): int(row[-1]) for row in reader}


def get_csv_inf(entry: str):
    if entry.endswith("/ет"):
        if entry.endswith("ы/ет"):
            return entry[0:-4] + "у"
        if entry.endswith("і/ет"):
            return entry[0:-4] + "у"
        if entry.endswith("и/ет"):
            return entry[0:-4] + "ию"
        if entry.endswith("й/ет"):
            return entry[0:-4] + "ю"
        if entry.endswith("п/ет"):
            return entry[0:-4] + "бу"
        if entry.endswith("қ/ет"):
            return entry[0:-4] + "ғу"
        if entry.endswith("к/ет"):
            return entry[0:-4] + "гу"
        return entry[:-3] + "у"
    return entry[: entry.rfind("/")]


usage = load_usage("jsons/usage.csv")


# from kaznlp.tokenization.tokhmm import TokenizerHMM
# from kaznlp.morphology.analyzers import AnalyzerDD
# from kaznlp.morphology.taggers import TaggerHMM
# import os

endings = [
    [
        "мын",
        "мiн",
        "бын",
        "бiн",
        "пын",
        "пiн",
        "сың",
        "сiң",
        "сыз",
        "сiз",
        "мыз",
        "мiз",
        "быз",
        "бiз",
        "пыз",
        "пiз",
        "сыңдар",
        "сiңдер",
        "сыздар",
        "сiздер",
        "дар",
        "дер",
        "тар",
        "тер",
        "лар",
        "лер",
        "м",
        "ң",
        "ңыз",
        "ңiз",
        "қ",
        "к",
        "ңдар",
        "ңдер",
        "ңыздар",
        "ңiздер",
        "",
    ],
    [
        "ның",
        "нің",
        "дың",
        "дің",
        "тың",
        "тің",
        "ға",
        "ге",
        "қа",
        "ке",
        "на",
        "не",
        "а",
        "е",
        "ды",
        "ді",
        "ты",
        "ті",
        "ны",
        "ні",
        "н",
        "да",
        "де",
        "та",
        "те",
        "нда",
        "нде",
        "дан",
        "ден",
        "тан",
        "тен",
        "нан",
        "нен",
        "мен",
        "бен",
        "пен",
        "",
    ],
    [
        "ым",
        "ім",
        "м",
        "ың",
        "ің",
        "ң",
        "ыңыз",
        "іңіз",
        "ңыз",
        "ңіз",
        "сы",
        "сі",
        "ы",
        "і",
        "ымыз",
        "іміз",
        "мыз",
        "міз",
        "",
    ],
    [
        "ып",
        "іп",
        "п",
        "а",
        "е",
        "й",
        "ды",
        "ді",
        "ты",
        "ті",
        "са",
        "се",
        "ар",
        "ер",
        "р",
        "ған",
        "ген",
        "қан",
        "кен",
        "атын",
        "етiн",
        "йтын",
        "йтін",
        "сын",
        "сін",
    ],
    ["дікі", "тікі", "нікі"],
    ["дар", "дер", "тар", "тер", "лар", "лер"],
    ["ба", "бе", "па", "пе", "ма", "ме"],
]

type comb_type = dict[int | None, comb_type | None]

combinations: comb_type = {
    0: {
        1: {None: None},
        3: {None: None, 6: {None: None}},
        5: {None: None},
        6: {None: None},
    },
    1: {2: {None: None, 5: {None: None}}},
    2: {None: None, 5: {None: None}},
    3: {None: None, 6: {None: None}},
    4: {None: None, 5: {None: None}},
    5: {None: None},
    6: {None: None},
}


def to_infinitive(
    initial: str, current: str, dic: comb_type, is_verb: bool
) -> tuple[str, bool]:
    if len(initial) <= 4:
        return initial.upper(), False
    max_removed_word = initial
    cur_is_verb = is_verb
    for key, val in dic.items():
        if key is None or val is None:
            if len(current) < len(max_removed_word):
                max_removed_word = current
        else:
            for ending in endings[key]:
                if current.endswith(ending):
                    if ending != "":
                        res_removed_word, is_verb_rec = to_infinitive(
                            initial, current[: -len(ending)], val, cur_is_verb
                        )
                    else:
                        res_removed_word, is_verb_rec = to_infinitive(
                            initial, current, val, cur_is_verb
                        )
                    cur_is_verb = cur_is_verb or is_verb_rec
                    if len(res_removed_word) < len(max_removed_word):
                        max_removed_word = res_removed_word
                        if key == 3:
                            cur_is_verb = True
    return max_removed_word.upper(), cur_is_verb


def get_init_fin(word: str):
    init = 0
    fin = len(word)
    while len(word) > 0 and word[0] in punctuation:
        word = word[1:]
        init += 1
    while len(word) > 0 and word[-1] in punctuation:
        word = word[:-1]
        fin -= 1
    return word, init, fin


GuessOptions = dict[str | None, list[str]]


class Guess(NamedTuple):
    word: str
    options: GuessOptions

    @override
    def __len__(self) -> int:
        return len(self.options)

    def __bool__(self) -> bool:
        return self.__len__() != 0


def transform(line: str, infs: dict[str, GuessOptions]):
    sentences = re.split(
        r"(?<!\w\.\w.)(?<![A-Z]\.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+", line
    )
    for j, sen in enumerate(sentences):
        if sen in tags:
            continue
        words = sen.split()
        guesses = list[Guess]()
        cur_guesses = list[Guess]()
        inits, fins = list[int](), list[int]()
        for i in range(len(words)):
            word = words[i]
            word, init, fin = get_init_fin(word)
            if len(word) != 0:
                result: Guess
                if any(map(lambda c: c.isdigit(), word)) or (
                    fins
                    and init == 0
                    and word[0].isupper()
                    and not words[i - 1] in "—–-"
                    and not words[i - 1][fins[i - 1] :] in ":"
                ):
                    result = Guess(word, {None: ["@"]})
                elif (
                    i + 1 < len(words)
                    and (
                        words[i][init:]
                        + " "
                        + words[i + 1][: get_init_fin(words[i + 1])[2]]
                    ).lower()
                    in infs.keys()
                ):
                    _, _, next_fin = get_init_fin(words[i + 1])
                    key = (words[i][init:] + " " + words[i + 1][:next_fin]).lower()
                    fin = len(words[i]) + 1 + next_fin
                    words[i] = words[i] + " " + words[i + 1]
                    result = Guess(key, get_inf(infs, key))
                    words[i + 1] = ""
                elif word.lower() in infs.keys():
                    result = Guess(word.lower(), get_inf(infs, word.lower()))
                    # if infs[word.lower()][1]:
                    #     result = (result[0].upper(), False)
                else:
                    res, is_verb = to_infinitive(
                        "=" + word, "=" + word, combinations, False
                    )
                    result = Guess(word, {None: [res + ("У" if is_verb else "")]})
                    # result = word.upper(), False
                    # eto dlya kirgizova
                if init != 0:
                    # apply_partial_rules(cur_guesses)
                    guesses.extend(cur_guesses)
                    cur_guesses = list[Guess]()
                cur_guesses.append(result)
                if fin != len(words[i]):
                    # apply_partial_rules(cur_guesses)
                    guesses.extend(cur_guesses)
                    cur_guesses = list[Guess]()
                inits.append(init)
                fins.append(fin)
            else:
                inits.append(init)
                fins.append(fin)
        # apply_partial_rules(cur_guesses)
        guesses.extend(cur_guesses)
        # apply_full_rules(guesses)
        k = 0
        for i in range(len(words)):
            if len(words[i]) != 0 and inits[i] != fins[i]:
                words[i] = (
                    words[i][: inits[i]]
                    + "\\~"
                    + words[i][inits[i] : fins[i]]
                    + "\\~"
                    + guess_to_text(guesses[k])
                    + "\\~"
                    + words[i][fins[i] :]
                )
                k += 1
        sentences[j] = " ".join(filter(None, words))
    return " ".join(sentences)


def apply_partial_rules(guesses: list[Guess]):
    # Rule 1: no verb-verb
    # Rule 2: no adj-verb
    pop_two_conseq(guesses, [("ет", "ет", "rule 1"), ("сн", "ет", "rule 2")])
    # Rule 3: ben, pen - homo
    for i in range(1, len(guesses) - 1):
        if guesses[i].word in {"бен", "пен"}:
            only1, only2 = get_only_option(guesses[i - 1]), get_only_option(
                guesses[i + 1]
            )
            if only1:
                if pop_except(guesses[i + 1], only1):
                    print("rule 3")
            elif only2:
                if pop_except(guesses[i - 1], only2):
                    print("rule 3")
    # Rule 5: san esim before zhyl
    for i in range(1, len(guesses)):
        if only_option(guesses[i], "зт") and guesses[i].options["зт"] == ["жыл"]:
            if pop_except(guesses[i - 1], "са"):
                print("rule 5")


def apply_full_rules(guesses: list[Guess]):
    # Rule 4: verb must be present
    active = True
    verb_options = None
    for i in range(len(guesses)):
        if only_option(guesses[i], "ет"):
            active = False
            break
        if "ет" in guesses[i].options:
            if not verb_options is None:
                active = False
                break
            verb_options = i
    if active:
        if verb_options is None:
            print(f"Rule 4 did not work on this sentence:\n{format_guesses(guesses)}")
        else:
            pop_except(guesses[verb_options], "ет")
            print("rule 4")


def get_only_option(guess: Guess):
    poses = list(guess.options.keys())
    if len(poses) != 1:
        return None
    return poses[0]


def only_option(guess: Guess, pos: str):
    return get_only_option(guess) == pos


def pop(guess: Guess, pos: str | None):
    pop = guess.options.pop(pos, None)
    if not guess.options:
        print(f"No options left for {pop} in sentence:")
        if not pop is None:
            guess.options[pos] = pop
    return bool(pop)


def pop_except(guess: Guess, pos: str):
    popped = False
    for cur_pos in list(guess.options.keys()):
        if cur_pos != pos:
            popped = popped or pop(guess, cur_pos)
    return popped


def pop_two_conseq(guesses: list[Guess], poses: list[tuple[str, str, str]]):
    for i in range(len(guesses)):
        for pos1, pos2, msg in poses:
            if i > 0 and only_option(guesses[i], pos2):
                if pop(guesses[i - 1], pos1):
                    print(msg)
            if i < len(guesses) - 1 and only_option(guesses[i], pos1):
                if pop(guesses[i + 1], pos2):
                    print(msg)


def get_inf(infs: dict[str, GuessOptions], key: str):
    data = infs[key]
    return data


def guess_to_text(guess: Guess):
    options = set[str]()
    for pos_options in guess.options.values():
        options |= set(pos_options)
    if len(options) == 1:
        return list(options)[0]
    return sorted(options, key=lambda option: usage.get(option, 0))[-1]


def format_guesses(guesses: list[Guess]):
    return ", ".join(map(guess_to_text, guesses))


# def transform_new(line):
#     mdl = os.path.join("kaznlp", "tokenization", "tokhmm.mdl")
#     tokhmm = TokenizerHMM(model=mdl)
#     sentences = tokhmm.tokenize(line)
#     analyzer = AnalyzerDD()
#     analyzer.load_model(os.path.join("kaznlp", "morphology", "mdl"))
#     tagger = TaggerHMM(lyzer=analyzer)
#     tagger.load_model(os.path.join("kaznlp", "morphology", "mdl"))
#     new_line = line
#     index = 0
#     for sentence in sentences:
#         lower_sentence = map(lambda x: x.lower(), sentence)
#         for i, a in enumerate(tagger.tag_sentence(lower_sentence)):
#             root = a.split()[0].split("_")[0]
#             if (a.split()[0].split("_")[2].startswith("ET")):
#                 root += "у"
#             if (sentence[i] in punctuation or sentence[i] == "*"):
#                 continue
#             where = index + new_line[index:].find(sentence[i])
#             new_line = new_line[:where] + "\\~" + new_line[where:where+len(
#                 sentence[i])] + "\\~" + root.upper() + "\\~" + new_line[where + len(sentence[i]):]
#             index = where + 6 + len(sentence[i] + root)
#     return new_line.strip()


if __name__ == "__main__":
    line = input()
    text = str()
    with codecs.open("scripts/infinitives.json", "r", "utf-8") as f:
        infs: dict[str, GuessOptions] = loads(f.read())
    while line != "finish":
        temp = list[str]()
        for sprint in line.split("\t"):
            temp.append(transform(sprint, infs))
        text += "\t".join(temp) + "\n"
        line = input()
    print(text)
