class Zotero {

  /** @type {AbortController} */
  static controller;

  // timeout 2 minutes
  static timeout = 2 * 60 * 1000;
  static isTimeout = false;
  static numberTimeouts = 0;

  static API_ENDPOINT = "zotero-api-endpoint";

  static API = {
    SELECTION_GET: this.API_ENDPOINT + "/selection/get",
    ITEM_ATTACHMENT_GET: this.API_ENDPOINT + "/attachment/get",
    LIBRARY_SEARCH: this.API_ENDPOINT + "/library/search",
    ITEM_CREATE: this.API_ENDPOINT + "/item/create",
    ITEM_UPDATE: this.API_ENDPOINT + "/item/update",
    ITEMS: this.API_ENDPOINT + "/items",
    CITATION_ADD: "cita/citation/add",
    CITATION_LIST: "cita/citation/list"
  }

  /**
   * Call the local Zotero server
   * @param {string} endpoint
   * @param {any} postData
   * @returns {Promise<*>}
   */
  static async callEndpoint(endpoint, postData = null) {
    this.controller = new AbortController();
    this.isTimeout = false;
    const timeoutFunc = () => {
      this.isTimeout = true;
      this.controller.abort();
    };
    const id = setTimeout(timeoutFunc, this.timeout);
    let result;
    try {
      let response = await fetch(Config.URL.ZOTERO_PROXY + "?" + endpoint, {
        method: postData ? "POST" : "GET",
        cache: 'no-cache',
        signal: this.controller.signal,
        headers: {
          'Content-Type': 'application/json'
        },
        body: postData ? JSON.stringify(postData) + '\r\n' : null
      });
      result = await response.text();
      if (result.toLowerCase().includes("endpoint")) {
        throw new Error(result.replace(/(endpoint)/i, "$1 " + endpoint));
      }
      result = JSON.parse(result);
      if (result.error) {
        throw new Error(result.error);
      }
      return result;
    } catch (e) {
      if (e.name === "AbortError" && this.isTimeout) {
        if (++this.numberTimeouts < 3) {
          return await this.callEndpoint(endpoint, postData);
        }
        this.numberTimeouts = 0;
        e = new Error(`Timeout trying to reach ${endpoint} (tried 3 times).`);
      }
      throw e;
    } finally {
      clearTimeout(id);
    }
  }

  /**
   * adapted from https://github.com/zotero/utilities/blob/4d8d7d3e92cbc3b4d62b82478e212a6f63b9a35f/utilities_item.js
   */
  static initZoteroSchema() {
    const data = this.CSL_SCHEMA;
    // CSL type/field mappings used by Utilities.Item.itemFromCSLJSON()
    Zotero.Schema.CSL_TYPE_MAPPINGS = {};
    Zotero.Schema.CSL_TYPE_MAPPINGS_REVERSE = {};
    for (let cslType in data.csl.types) {
      for (let zoteroType of data.csl.types[cslType]) {
        Zotero.Schema.CSL_TYPE_MAPPINGS[zoteroType] = cslType;
      }
      Zotero.Schema.CSL_TYPE_MAPPINGS_REVERSE[cslType] = [...data.csl.types[cslType]];
    }
    Zotero.Schema.CSL_TEXT_MAPPINGS = data.csl.fields.text;
    Zotero.Schema.CSL_DATE_MAPPINGS = data.csl.fields.date;
    Zotero.Schema.CSL_NAME_MAPPINGS = data.csl.names;
    Zotero.Schema.CSL_FIELD_MAPPINGS_REVERSE = {};
    for (let cslField in data.csl.fields.text) {
      for (let zoteroField of data.csl.fields.text[cslField]) {
        Zotero.Schema.CSL_FIELD_MAPPINGS_REVERSE[zoteroField] = cslField;
      }
    }
    for (let cslField in data.csl.fields.date) {
      let zoteroField = data.csl.fields.date[cslField];
      Zotero.Schema.CSL_FIELD_MAPPINGS_REVERSE[zoteroField] = cslField;
    }
  }

  /**
   * Converts an item in CSL JSON format to a Zotero item
   * adapted from https://github.com/zotero/utilities/blob/4d8d7d3e92cbc3b4d62b82478e212a6f63b9a35f/utilities_item.js
   * @param {Object} cslItem
   */
  static itemFromCSLJSON(cslItem) {
    // zotero schema
    if (!Zotero.Schema.CSL_TYPE_MAPPINGS) {
      this.initZoteroSchema()
    }

    // new item
    const item = {
      creators: []
    }

    // item type
    if (!cslItem.type) {
      throw new Error("No 'type' provided in CSL-JSON");
    }
    let zoteroType;
    if (cslItem.type === 'bill' && (cslItem.publisher || cslItem['number-of-volumes'])) {
      zoteroType = 'hearing';
    } else if (cslItem.type === 'broadcast'
      && (cslItem['archive']
        || cslItem['archive_location']
        || cslItem['container-title']
        || cslItem['event-place']
        || cslItem['publisher']
        || cslItem['publisher-place']
        || cslItem['source'])) {
      zoteroType = 'tvBroadcast';
    } else if (cslItem.type === 'book' && cslItem.version) {
      zoteroType = 'computerProgram';
    } else if (cslItem.type === 'song' && cslItem.number) {
      zoteroType = 'podcast';
    } else if (cslItem.type === 'motion_picture'
      && (cslItem['collection-title'] || cslItem['publisher-place']
        || cslItem['event-place'] || cslItem.volume
        || cslItem['number-of-volumes'] || cslItem.ISBN)) {
      zoteroType = 'videoRecording';
    } else if (Zotero.Schema.CSL_TYPE_MAPPINGS_REVERSE[cslItem.type]) {
      zoteroType = Zotero.Schema.CSL_TYPE_MAPPINGS_REVERSE[cslItem.type][0];
    } else {
      console.log(`Unknown CSL type '${cslItem.type}' -- using 'document'`, 2);
      zoteroType = "document"
    }
    item.itemType = zoteroType;

    // map text fields
    for (let [cslField, zoteroFields] of Object.entries(Zotero.Schema.CSL_TEXT_MAPPINGS)) {
      if (cslField in cslItem) {
          item[zoteroFields[0]] = cslItem[cslField];
      }
    }

    // translate creators
    for (let [zoteroCreatorType, cslCreatorType] of Object.entries(Zotero.Schema.CSL_NAME_MAPPINGS)) {
      if (cslCreatorType in cslItem) {
        let nameMappings = cslItem[cslCreatorType];
        for (let cslCreator of nameMappings) {
          let creator = {};
          if (cslCreator.family && cslCreator.given) {
            creator.lastName = cslCreator.family || '';
            creator.firstName = cslCreator.given || '';
          } else if (cslCreator.literal) {
            creator.lastName = cslCreator.literal;
            creator.fieldMode = 1;
          } else {
            creator.lastName =  cslCreator.family || cslCreator.given || "unknown";
            creator.fieldMode = 1;
          }
          creator.creatorType = zoteroCreatorType
          item.creators.push(creator);
        }
      }
    }

    // date
    for (let [cslDateField, zoteroDateField] of Object.entries(Zotero.Schema.CSL_DATE_MAPPINGS)) {
      if (cslDateField in cslItem) {
        item[zoteroDateField] = cslItem[cslDateField];
      }
    }
    return item
  }


  /**
   * Returns a map of keys and items
   * @param {number} libraryID
   * @param {string[]} keys
   * @returns {Promise<{}>}
   */
  static async getItemAttachments(libraryID, keys) {
    return await this.callEndpoint(this.API.ITEM_ATTACHMENT_GET, {
      libraryID, keys
    });
  }

  /**
   * @returns {Promise<{libraryID: number|null, groupID: number|null, selectedItems: object[], collection: string|null, childItems: object[]}>}
   */
  static async getSelection() {
    return await this.callEndpoint(this.API.SELECTION_GET);
  }

  /**
   * @param {number} libraryID
   * @param {object} query
   * @param {string} resultType
   * @returns {Promise<object[]>}
   */
  static async search(libraryID, query, resultType = "items") {
    return await this.callEndpoint(this.API.LIBRARY_SEARCH, {
      libraryID,
      query,
      resultType
    })
  }

  /**
   * Create one or more new items in a Zotero library
   * @param {number} libraryID
   * @param {object[]} items
   * @param {string[]|null} collections
   * @returns {Promise<string[]>}
   */
  static async createItems(libraryID, items, collections = null) {
    return await this.callEndpoint(this.API.ITEM_CREATE, {
      libraryID,
      collections,
      items
    });
  }

  /**
   * Update one or more new items in a Zotero library
   * @param {number} libraryID
   * @param {object[]} items
   * @returns {Promise<string[]>}
   */
  static async updateItems(libraryID, items) {
    return await this.callEndpoint(this.API.ITEM_UPDATE, {
      libraryID,
      items
    });
  }


  /**
   * Add items in a Zotero library as citations to a source item
   * @param {number} libraryID  The library ID for the source and cited items
   * @param {string} sourceItemKey The item key of the source item
   * @param {string[]} citedItemKeys An array of the item keys for the cited items
   * @returns {Promise<string>} statusMessage - Result of the operation.
   */
  static async addCitations(libraryID, sourceItemKey, citedItemKeys) {
    return await this.callEndpoint(this.API.CITATION_ADD, {
      libraryID,
      sourceItemKey,
      citedItemKeys
    });
  }

  /**
   * list the cited references of an item
   * @param {number} libraryID  The library ID for the source and cited items
   * @param {string} sourceItemKey The item key of the source item
   * @returns {Promise<object[]>}
   */
  static async listCitations(libraryID, sourceItemKey) {
    return await this.callEndpoint(this.API.CITATION_LIST, {
      libraryID,
      sourceItemKey
    });
  }

  /**
   * Retrieve the items data for the given keys
   * @param {number} libraryID  The library ID for the source and cited items
   * @param {string[]} keys The item keys of the requested items
   * @returns {Promise<object[]>}
   */
  static async items(libraryID, keys) {
    return await this.callEndpoint(this.API.ITEMS, {
      libraryID,
      keys
    });
  }

  static CSL_SCHEMA = {
    "csl": {
      "types": {
        "article": [
          "preprint"
        ],
        "article-journal": [
          "journalArticle"
        ],
        "article-magazine": [
          "magazineArticle"
        ],
        "article-newspaper": [
          "newspaperArticle"
        ],
        "bill": [
          "bill"
        ],
        "book": [
          "book"
        ],
        "broadcast": [
          "podcast",
          "tvBroadcast",
          "radioBroadcast"
        ],
        "chapter": [
          "bookSection"
        ],
        "document": [
          "document",
          "attachment",
          "note"
        ],
        "entry-dictionary": [
          "dictionaryEntry"
        ],
        "entry-encyclopedia": [
          "encyclopediaArticle"
        ],
        "graphic": [
          "artwork"
        ],
        "hearing": [
          "hearing"
        ],
        "interview": [
          "interview"
        ],
        "legal_case": [
          "case"
        ],
        "legislation": [
          "statute"
        ],
        "manuscript": [
          "manuscript"
        ],
        "map": [
          "map"
        ],
        "motion_picture": [
          "film",
          "videoRecording"
        ],
        "paper-conference": [
          "conferencePaper"
        ],
        "patent": [
          "patent"
        ],
        "personal_communication": [
          "letter",
          "email",
          "instantMessage"
        ],
        "post": [
          "forumPost"
        ],
        "post-weblog": [
          "blogPost"
        ],
        "report": [
          "report"
        ],
        "software": [
          "computerProgram"
        ],
        "song": [
          "audioRecording"
        ],
        "speech": [
          "presentation"
        ],
        "thesis": [
          "thesis"
        ],
        "webpage": [
          "webpage"
        ]
      },
      "fields": {
        "text": {
          "abstract": [
            "abstractNote"
          ],
          "archive": [
            "archive"
          ],
          "archive_location": [
            "archiveLocation"
          ],
          "authority": [
            "court",
            "legislativeBody",
            "issuingAuthority"
          ],
          "call-number": [
            "callNumber",
            "applicationNumber"
          ],
          "chapter-number": [
            "session"
          ],
          "collection-number": [
            "seriesNumber"
          ],
          "collection-title": [
            "seriesTitle",
            "series"
          ],
          "container-title": [
            "publicationTitle",
            "reporter",
            "code"
          ],
          "dimensions": [
            "artworkSize",
            "runningTime"
          ],
          "DOI": [
            "DOI"
          ],
          "edition": [
            "edition"
          ],
          "event-place": [
            "place"
          ],
          "event-title": [
            "meetingName",
            "conferenceName"
          ],
          "genre": [
            "type",
            "programmingLanguage"
          ],
          "ISBN": [
            "ISBN"
          ],
          "ISSN": [
            "ISSN"
          ],
          "issue": [
            "issue",
            "priorityNumbers"
          ],
          "journalAbbreviation": [
            "journalAbbreviation"
          ],
          "language": [
            "language"
          ],
          "license": [
            "rights"
          ],
          "medium": [
            "medium",
            "system"
          ],
          "note": [
            "extra"
          ],
          "number": [
            "number"
          ],
          "number-of-pages": [
            "numPages"
          ],
          "number-of-volumes": [
            "numberOfVolumes"
          ],
          "page": [
            "pages"
          ],
          "publisher": [
            "publisher"
          ],
          "publisher-place": [
            "place"
          ],
          "references": [
            "history",
            "references"
          ],
          "scale": [
            "scale"
          ],
          "section": [
            "section",
            "committee"
          ],
          "shortTitle": [
            "shortTitle"
          ],
          "source": [
            "libraryCatalog"
          ],
          "status": [
            "legalStatus"
          ],
          "title": [
            "title"
          ],
          "title-short": [
            "shortTitle"
          ],
          "URL": [
            "url"
          ],
          "version": [
            "versionNumber"
          ],
          "volume": [
            "volume",
            "codeNumber"
          ]
        },
        "date": {
          "accessed": "accessDate",
          "issued": "date",
          "submitted": "filingDate"
        }
      },
      "names": {
        "author": "author",
        "bookAuthor": "container-author",
        "castMember": "performer",
        "composer": "composer",
        "contributor": "contributor",
        "director": "director",
        "editor": "editor",
        "guest": "guest",
        "interviewer": "interviewer",
        "producer": "producer",
        "recipient": "recipient",
        "reviewedAuthor": "reviewed-author",
        "seriesEditor": "collection-editor",
        "scriptwriter": "script-writer",
        "translator": "translator"
      }
    },
  }
  static Schema = {}
}
