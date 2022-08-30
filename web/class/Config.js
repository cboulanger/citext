class Config {
  static channel_id;
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
    SPAN: /<\/?span[^>]*>/ig,
    DIV: /<\/?div[^>]*>/ig,
    BR: /<br[^>]*>/ig,
    PUNCTUATION: /\p{P}/gu,
    LAYOUT: /(\t[^\t]+){6}/g,
    EMPTY_NODE: /<[^>]+><\/[^>]+>/g,
    DATA_TAG_SPAN: /<span data-tag="([^"]+)"[^<]*>([^<]*)<\/span>/gm,
    PAGE_NUMBER_IN_LINE: /^[0-9]{1,3}|[0-9]{1,3}/
  }
  static KNOWN_IDENTIFIERS = [
    {
      startsWith: "10.",
      cslJson: "doi",
      zoteroField: "DOI"
    },
    {
      startsWith: "978",
      cslJson: "isbn",
      zoteroField: "ISBN"
    }
  ]
  static SIGNAL_WORDS = [
    /(see |cf\.? |e\.g\. |accord )(also )?/i,
    /(siehe |vgl. )?(dazu |hierzu )?(etwa |näher )?(auch)?/i,
    /(anders )(etwa )/i,
  ]
}

