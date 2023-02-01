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
    DATA_TAG_SPAN: /<span data-tag="([^"]+)"[^>]*>([^<]*)<\/span>/gm,
    PAGE_NUMBER_IN_LINE: /^[0-9]{1,3}|[0-9]{1,3}/,
    FOOTNOTE_NUMBER_AT_LINE_START: /^([\d]{1,3}\.?\s+)(\p{L}.{30,})$/iu,
    DASH_AT_LINE_END: /[\s\u00AD\u002D\u058A\u05BE\u1400\u1806\u2010\u2011\u2012\u2053\u207B\u208B\u2212\uFE58\uFE63]+$/gu
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
      // English
      /(see, )(for example, |on the contrary, |on the other hand, |generally, )/gi,
      /(see )(the discussion in )/gi,
      /(also |although )?(see,? |cf\.? |e\.g\.,? |accord |compare )(also ,?)?/ig,
      /(also, |similarly, |alternatively, )/ig,
      /(as )?(discussed |detailed |described |cited )(in |by )/ig,
      /(on |regarding )([^,]+, )(see )(also )?/ig,
      /(first )?(published as |reprinted in )/gi,
      // German
      /(anders |ähnlich |ausführlich )(etwa |auch )/gi,
      /(sowie)( bei |[: ]+)/gi,
      /(zitiert)( als| in| bei)?[: ]+/gi,
      /(zuerst | wieder )?(abgedruckt |zitiert |überarbeitet |erscheint )(als|in)[: ]+/gi,
      /(speziell |insbesondere |ausführlich |beispielsweise )(zu[rm]? )([^.;,]+?):/gi,
      /(siehe |s\. )?(zu[mr]?)( .+? )(ausführlich |beispielsweise )/gi,
      /(als überblick|allgemein)( zu .+?)?: ?/gi,
      /(mit Hinweis auf )/gi,
      /(unter vielen )/gi,
      /(dazu |hierzu )(ausführlich |etwa |näher )?(auch )?(meinen beitrag |den beitrag von )?[: ]*?/gi,
      /(siehe |vgl\. )/gi
    ],
    END_CITATION: [
      /([\d]+\s*)(-\s*)?([\d]+\s*)?(ff| (et |and )?passim)?\s*([;.]\s*)/gi,
      /\d+, at \d+\. /gi,
      /\d+, and /gi
    ]
  }
  static BACKREFERENCES = {
    PREVIOUS_FOOTNOTE: [/ (fn|n|)\./i, /(fußnote|note)/i],
    PREVIOUS_PUBLICATION: [/(ebd|a\.a\.o|ibid|op\. cit)\./i],
    PREVIOUS_AUTHOR: [/(ders|dies)/i, /^[_-]{3}/]
  }
}

