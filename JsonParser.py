
import re
from collections import OrderedDict
import json

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
        except Exception,e:
            print e.message
        
