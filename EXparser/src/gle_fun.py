# -*- coding: UTF-8 -*- 
# Definition: general function for extraction and segemntation

import re, os

list_dir = '/app/Exparser/lists/'

# list of stop words  (it is better to make them in a file)
stopw = r'\bgewesen\b|\beines\b|\bim\b|\bselbst\b|\bdu\b|\bkeinen\b|\bmancher\b|\bsollte\b|\bkein\b|\beurem\b|\bjeder\b|\bhinter\b|\bmich\b|\bihres\b|\bmeiner\b|\balles\b|\bwelcher\b|\bals\b|\bhatten\b|\bihren\b|\bdein\b|\bwieder\b|\bwird\b|\bzum\b|\bderselbe\b|\bnach\b|\bviel\b|\bwas\b|\bsie\b|\bnoch\b|\bsolches\b|\betwas\b|\beiniger\b|\bob\b|\beinige\b|\beinmal\b|\bkeinem\b|\bin\b|\bohne\b|\bseinem\b|\bda\b|\bweg\b|\bweil\b|\bein\b|\bderer\b|\bgegen\b|\bseines\b|\bwill\b|\bjener\b|\bwaren\b|\bnur\b|\banderm\b|\baber\b|\bjenen\b|\bbin\b|\bweiter\b|\bwir\b|\bdeines\b|\bjeden\b|\bdiesen\b|\bkoennte\b|\bkeine\b|\bdiese\b|\bvom\b|\bwelchem\b|\bdessen\b|\baus\b|\bwerden\b|\beure\b|\bwirst\b|\banderr\b|\bjenem\b|\bso\b|\bwelches\b|\bmanchen\b|\bzwischen\b|\bes\b|\ballem\b|\bins\b|\beurer\b|\bunserem\b|\bmusste\b|\bnichts\b|\bdort\b|\bden\b|\bihre\b|\bjene\b|\banderem\b|\bdir\b|\bdemselben\b|\bmeines\b|\bdass\b|\beine\b|\bdieses\b|\bder\b|\bdazu\b|\bvon\b|\bwerde\b|\bmeine\b|\bich\b|\bseinen\b|\bwuerden\b|\bwollen\b|\bdies\b|\bseiner\b|\bwar\b|\bdeiner\b|\banders\b|\boder\b|\bindem\b|\bauch\b|\bbist\b|\buns\b|\bkeines\b|\bdieselbe\b|\bmein\b|\bihrem\b|\bderselben\b|\bdas\b|\bander\b|\beiniges\b|\bmachen\b|\bsonst\b|\bund\b|\bkann\b|\bsehr\b|\bdieser\b|\bihr\b|\bhab\b|\bbis\b|\bsein\b|\bunser\b|\bwaehrend\b|\banderen\b|\bauf\b|\bdesselben\b|\ballen\b|\bdeinen\b|\bwollte\b|\bkeiner\b|\ber\b|\bseine\b|\beinig\b|\bman\b|\balso\b|\bdiesem\b|\bdamit\b|\bjenes\b|\bmanche\b|\banderes\b|\bmuss\b|\beinem\b|\bdeine\b|\bdasselbe\b|\bsondern\b|\bhatte\b|\bvor\b|\beinigem\b|\bhaben\b|\bmeinem\b|\bhat\b|\bsoll\b|\bunsere\b|\bihrer\b|\balle\b|\bandern\b|\bdann\b|\bist\b|\bwenn\b|\bwie\b|\bzu\b|\bdoch\b|\bzwar\b|\bmanchem\b|\beuren\b|\bdich\b|\bwelchen\b|\bdeinem\b|\bdes\b|\beinigen\b|\bmir\b|\bhabe\b|\bmit\b|\bzur\b|\bdem\b|\beuch\b|\bhier\b|\beiner\b|\bkoennen\b|\bwarst\b|\bdie\b|\bsolchem\b|\bsind\b|\bwuerde\b|\bdurch\b|\bmeinen\b|\beures\b|\bsich\b|\bam\b|\beinen\b|\bjetzt\b|\bnun\b|\bnicht\b|\bihnen\b|\ban\b|\bsolcher\b|\bsolchen\b|\bdenselben\b|\bdieselben\b|\bunter\b|\banderer\b|\bbei\b|\beuer\b|\bueber\b|\bandere\b|\bwo\b|\bdenn\b|\bum\b|\bhin\b|\bunseren\b|\bjedem\b|\baller\b|\bfuer\b|\bsolche\b|\bjedes\b|\bmanches\b|\bunseres\b|\bwelche\b|\bihn\b|\bjede\b|\bihm\b'
# with  open(list_dir + "stopwords.csv", "r") as file:
# todo: join stopwords to raw string above

def read_words_from_file(filename):
    path = list_dir + filename
    # check for local override
    if (os.path.isfile(path + ".local.csv")):
        path += ".local"
    with open(path + ".csv", "r") as file:
        return set(file.readlines())


# read word lists into variables
b1 = read_words_from_file("names")
b2 = read_words_from_file("abv")
b3 = read_words_from_file("cities")
b4 = read_words_from_file("edt")
b5 = read_words_from_file("journals")
b6 = read_words_from_file("publishers")

# make text lower
def textlow(ln):
    ln = re.sub(r'[Ää]', 'ae', ln)
    ln = re.sub(r'[Üü]', 'ue', ln)
    ln = re.sub(r'[Öö]', 'oe', ln)
    ln = re.sub(r'Ï', 'ï', ln)
    ln = re.sub(r'È', 'è', ln)
    ln = re.sub(r'É', 'é', ln)
    ln = re.sub(r'Ç', 'ç', ln)
    ln = re.sub(r'Â', 'â', ln)
    ln = re.sub(r'Î', 'î', ln)
    ln = re.sub(r'Ô', 'ô', ln)
    ln = re.sub(r'Ê', 'ê', ln)
    ln = re.sub(r'Ë', 'ë', ln)
    ln = re.sub(r'Ù', 'ù', ln)
    ln = re.sub(r'Ì', 'ì', ln)
    ln = re.sub(r'Ò', 'ò', ln)
    ln = re.sub(r'À', 'à', ln)
    ln = re.sub(r'Ã', 'ã', ln)
    ln = re.sub(r'Õ', 'õ', ln)
    ln = re.sub(r'Ñ', 'ñ', ln)
    ln = re.sub(r'Û', 'û', ln)
    ln = re.sub(r'ß', 'ss', ln)
    ln = ln.lower()
    return ln
