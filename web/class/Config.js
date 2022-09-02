class Config {
  /* The url of the exparser backend */
  static SERVER_URL = "/cgi-bin/"
  static URL = {
    SERVER: "/cgi-bin/",
    UPLOAD: "/cgi-bin/upload.rb",
    ZOTERO_PROXY: "/cgi-bin/zotero/proxy.py",
    LOAD_FROM_URL: "/cgi-bin/load-from-url.py"
  }
  static ENGINES = {
    ANYSTYLE: "anystyle",
    EXPARSER: "exparser"
  }
  static LOCAL_STORAGE = {
    DOCUMENT: "excite_document",
    TEXT_FILE_NAME: "excite_text_file_name",
    PDF_IFRAME_SRC: "excite_pdf_iframe_source",
    LAST_LOAD_URL: "excite_last_load_url",
    LAST_MODEL_NAME: "excite_last_model_name"
  }
  static REGEX = {
    TAG: /<\/?[^>]+>/g,
    TAG_OPEN: /<[^>/]+>/g,
    TAG_CLOSE: /<\/[^>]+>/g,
    SPAN: /<\/?span[^>]*>/ig,
    DIV: /<\/?div[^>]*>/ig,
    BR: /<br[^>]*>/ig,
    PUNCTUATION: /\p{P}/gu,
    LAYOUT: /(\t[^\t]+){6}/g,
    EMPTY_NODE: /<[^>]+><\/[^>]+>/g,
    DATA_TAG_SPAN: /<span data-tag="([^"]+)"[^<]*>([^<]*)<\/span>/gm,
    PAGE_NUMBER_IN_LINE: /^[0-9]{1,3}|[0-9]{1,3}/,
    FOOTNOTE_NUMBER_AT_LINE_START: /^([\d]{1,3}\s+)(\p{L}.{30,})$/iu
  }
  static KNOWN_IDENTIFIERS = [
    {
      name: "doi",
      match: /^(?<DOI>10.\d{4,9}\/[-._;()/:A-Z0-9]+)$/i,
    },
    {
      name: "isbn",
      match: /^(?<ISBN>978[0-9-]+)/,
    },
    {
      name: "author-date-title",
      match: /^(?<author>[\S]+)[-_( ]+(?<date>[0-9.]+)[-_) ]+(?<title>.+)$/,
    },
    {
      name: "key",
      match: /^(?<key>[A-Z0-9]{8})$/,
    }
  ]
  static SIGNAL_WORDS = {
    START_CITATION: [
      /(see, )(for example, |on the contrary, |on the other hand, |generally, )/gi,
      /(also |although )?(see,? |cf\.? |e\.g\.,? |accord |compare )(also ,?)?/ig,
      /(also, |similarly, )/ig,
      /(siehe |vgl\. |näher |etwa | beispielsweise )(dazu |hierzu )?(etwa |näher )?(auch )?/gi,
      /(dazu |hierzu )(etwa |näher )?(auch)?/gi,
      /(anders etwa |ähnlich auch )/gi,
      /(sowie )(bei )?/gi,
      /(zitiert:|zitiert als:?)/gi,
      /(zuerst )?(abgedruckt in:?|zitiert als:?)/gi,
      /(first )?(published as |reprinted in )/gi
    ],
    END_CITATION: [
      /([\d]+\s*)(-\s*)?([\d]+\s*)?(ff| (et |and )?passim)?\s*([;.]\s*)/gi,
      /\d+, at \d+\. /gi,
      /\d+, and /gi
    ]
  }
  static BACKREFERENCES ={
    PREVIOUS_FOOTNOTE: [/ (fn|n|)\./i, /(fußnote|note)/i],
    PREVIOUS_PUBLICATION: [/(ebd|a\.a\.o|ibid|op\. cit)\./i],
    PREVIOUS_AUTHOR: [/(ders|dies)/i, /^[_-]{3}/]
  }
}

