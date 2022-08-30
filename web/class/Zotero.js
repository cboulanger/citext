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
      if (result.includes("Endpoint")) {
        throw new Error(result.replace("Endpoint", "Endpoint " + endpoint));
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
   * @param {string} ref
   * @returns {{date: *, volume: *, pages: (*|undefined), issue: *, ISBN: (*|undefined), creators: *[], publisher: *, title: *, publicationTitle: *, URL: *, DOI: (*|undefined)}}
   */
  static convertRefsToJson(ref) {
    function extract(tagName, text) {
      let regexp = new RegExp(`<${tagName}>(.*?)</${tagName}>`, "g");
      let m;
      let result = [];
      while (m = regexp.exec(text)) {
        result.push(m[1])
      }
      return result.length ? result : undefined;
    }

    let tags = [
      "author", "title", "source",
      "editor", "year", "volume", "issue",
      "publisher", "fpage", "lpage", "url", "identifier"
    ];
    const r = {};
    for (let tag of tags) {
      r[tag] = extract(tag, ref);
    }
    let creators = [];
    if (r.author) {
      for (let author of r.author) {
        const firstName = extract("given-names", author)?.[0];
        const lastName = extract("surname", author)?.[0];
        if (firstName && lastName) {
          creators.push({
            "creatorType": "author",
            firstName,
            lastName
          });
        } else {
          creators.push({
            "creatorType": "author",
            "name": lastName || firstName
          });
        }
      }
    }
    if (r.editor) {
      for (let editor of r.editor) {
        creators.push({
          "creatorType": "editor",
          "name": editor
        });
      }
    }
    let item = {
      creators,
      "title": r.title?.[0],
      "date": r.year?.[0],
      "volume": r.volume?.[0],
      "issue": r.issue?.[0],
      "publisher": r.publisher?.[0],
      "pages": r.fpage?.[0] ? (r.fpage?.[0] + (r.lpage?.[0] ? "-" + r.lpage?.[0] : "")) : undefined,
      "URL": r.url?.[0],
      "DOI": r.identifier?.[0]?.startsWith("10.") ? r.identifier?.[0] : undefined,
      "ISBN": r.identifier?.[0]?.startsWith("978") ? r.identifier?.[0] : undefined,
    };
    let source = r.source?.[0];
    if (!source) {
      item.itemType = "book";
      delete item.pages;
      delete item.issue;
    } else if (item.publisher || !item.volume) {
      item.itemType = "bookSection";
      item.bookTitle = source;
      delete item.issue;
    } else {
      item.itemType = "journalArticle";
      item.publicationTitle = source;
      delete item.publisher;
    }
    return item;
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
   * @returns {Promise<object[]>} statusMessage - Result of the operation.
   */
  static async listCitations(libraryID, sourceItemKey) {
    return await this.callEndpoint(this.API.CITATION_LIST, {
      libraryID,
      sourceItemKey
    });
  }
}
