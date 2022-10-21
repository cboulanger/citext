class Annotation {
  static type;
  static engine;
  static fileExtension;
  static TYPE = {
    FINDER: "finder",
    PARSER: "parser"
  }
  static mimeType;

  constructor(content, fileName) {
    this.content = content.replace(/\r/g, "");
    this.tags = []
    const dateString = (new Date()).toISOString().replace(/[T]/g, "_").replace(/[-:Z.]/g, "")
    this.fileName = fileName || "annotation-" + dateString + "." + this.getFileExtension()
  }

  load(text) {
    throw new Error("Implemented by subclass")
  }

  getEngine() {
    return this.constructor.engine;
  }

  getFileName() {
    return this.fileName;
  }

  getType() {
    return this.constructor.type;
  }

  getFileExtension() {
    return this.constructor.fileExtension;
  }

  getMimeType() {
    return this.constructor.mimeType;
  }

  getContent() {
    return this.content
  }

  setContent(content) {
    this.content = content.trim();
  }

  toHtml() {
    return this._markupToHtml(this.getContent());
  }

  /**
   * Returns the marked-up text. This is an internal representation, to
   * be able to check the marked up text. To get the correct format
   * suitable to be saved in a file and used by the parser engine, use #export()
   * @returns {string}
   */
  toMarkup() {
    return this.content
  }

  /**
   * Exports the content for saving in a file in the correct format used
   * by the parser engine
   * @returns {string}
   */
  export() {
    return this.toMarkup()
  }

  /**
   * Translates the html code from the editor to the internal markup
   * @param {string} html
   * @return {string}
   */
  loadFromHtml(html) {
    let markedUpText = html
      .replace(Config.REGEX.DIV, "")
      .replace(/<span[^>]*>(<br>)<\/span>/g,"<br>")
      .replace(/<span[^>]*> *<\/span>/g,"<br>")
      .replace(Config.REGEX.BR, "\n")
      .replace(Config.REGEX.DATA_TAG_SPAN, "<$1>$2</$1>")


    // check if translation removed all <span> tags and warn if not
    if (markedUpText.match(Config.REGEX.SPAN)) {
      console.warn("Removing unhandled <span> tags in html text!");
      markedUpText = markedUpText.replace(Config.REGEX.SPAN, "");
    }
    this.content = markedUpText.trim()
    return this.content
  }

  /**
   * Final cleanup of text
   * @param {string} text
   * @returns {string}
   * @private
   */
  static removeXmlEntities(text) {
    return text
      .replace(/&amp;/g, "&")
      .replace(/&gt;/g, ">")
      .replace(/&lt;/g, "<")
      .replace(/&quot;/g, '"')
      .replace(/&pos;/g, "'")
      .replace(/&nbsp;/g, " ")
      .trim();
  }

  /**
   * Given a text with xml-style markup, return HTML that displays this markup visually
   * also populates `this.tags`
   * @param {string} text
   * @returns {string}
   */
  _markupToHtml(text) {
    // translate tag names to data-tag attributes
    let tag_names = [];
    let tag_name;
    for (let match of text.matchAll(/<([^>\/ ]+)>/g)) {
      tag_name = match[1];
      if (!tag_names.includes(tag_name)) {
        tag_names.push(tag_name);
      }
    }
    this.tags = tag_names;
    for (tag_name of tag_names) {
      let regex = new RegExp(`<${tag_name}>(.*?)</${tag_name}>`, 'gs');
      let replacement = `<span data-tag="${tag_name}">$1</span>`;
      text = text.replace(regex, replacement);
    }
    // convert line breaks to break nodes
    return text.replace(/\n/g, "<br>").trim();
  }

  _htmlToMarkup(html) {
    return html
      .replace(Config.REGEX.DIV, "")
      .replace(Config.REGEX.BR, "\n")
      .replace(Config.REGEX.DATA_TAG_SPAN, "<$1>$2</$1>")
      .trim()
  }
}

class FinderAnnotation extends Annotation {

  extractReferences() {
    throw new Error("Implemented by subclass")
  }

  toParserAnnotation() {
    throw new Error("Implemented by subclass")
  }
}

class ParserAnnotation extends Annotation {
  numRefs = 0;
  toFinderAnnotation() {
    throw new Error("Implemented by subclass")
  }
}
