
import re
from collections import OrderedDict
import json

refString='<author><surname prob="0.9898">Gade</surname><given-names prob="0.8888">Peter </given-names></author>  <author><surname prob="0.9300">Grabner</surname>,<given-names prob="0.9645">Petra</given-names><given-names prob="0.89898">W.</given-names></author>/Helge<author><given-names prob="0.6822">Torgersen</given-names></author> (<year prob="0.9671">1998</year>). <title prob="0.9794">Osterreichs</title><title prob="0.9849">Gentechnikpolitik</title><title prob="0.9517">-</title><title prob="0.9945">Technikkritische</title><title prob="0.9971">Vorreiterrolle</title><title prob="0.9966">oder</title><title prob="0.9952">Modernisierungsverweigerung</title>?, in: <source prob="0.9966">Osterreichische</source><source prob="0.9983">Zeitschrift</source><source prob="0.9962">fur</source> <source prob="0.9777">Politikwissenschaft</source>, <volume prob="0.9967">27</volume> (<issue prob="0.9971">1</issue>), <fpage prob="0.9753">5</fpage>-<lpage prob="0.9983">27</lpage>' 
refString='(<year prob="0.9970">2007a</year>), <title prob="0.9904">OECD</title> <title prob="0.9928">work</title> <title prob="0.9923">on</title> <title prob="0.9914">patents</title> <title prob="0.9864">-</title> <title prob="0.9881">Patent</title> <title prob="0.9818">Database,</title> <title prob="0.8261">Organisation</title> <title prob="0.8213">for</title> <title prob="0.8145">Economic</title> <title prob="0.8006">Co-Operation</title> <title prob="0.7891">and</title> <title prob="0.7681">Development</title>, <<source prob="0.7832">http://www.oecd.org/document/10/0</source>, <source prob="0.5156">2340</source>, <other prob="0.8095">en_2649_34451_1901066_1_1_1</other> _<other prob="0.5814">1</other>, <other prob="0.7106">00.html</other>>.'

##refString=re.sub(r'<author>|</author>', '', refString)

def createJson(refString):
    if refString is not None and len(refString.strip())>0:
        try:                    
            refString=re.sub(r'"',"",refString)
            xml_pattern = re.compile("(?P<open><(?P<tag>[a-z-]*?) prob=(?P<prbob>[0-9\.]+)>)(?P<text>.*?)(?P<close></(?P=tag)>)")
            tagDictionary=OrderedDict()
            temp_list = []
            for item in xml_pattern.finditer(refString):
                data={}
                itemdict=item.groupdict()
                ctag=itemdict['tag']
                if ctag=="fpage" or ctag=="lpage":
                    tag="page"
                elif ctag=="given-names" or ctag=="surname":
                    tag="author"
                else:
                    tag=ctag
                    
                if tag not in tagDictionary.keys():
                    tagDictionary[tag]=[]
               
                tagDictionaryVal=tagDictionary[tag]
                data["score"]=itemdict['prbob']
                if tag=="author":
                    data[ctag]=itemdict['text']
                else:
                    data["value"]=itemdict['text']
                if tag=="author":
                    tagDictionaryVal.append([data])
                else:
                    tagDictionaryVal.append(data)
                    
                tagDictionary[tag]=tagDictionaryVal
            return json.dumps(tagDictionary)
            # return tagDictionary
        except Exception,e:
            print e.message
            
    
# print createJson(refString)
        
