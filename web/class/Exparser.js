class ExparserExtractionAnnotation extends FinderAnnotation {
  static type = Annotation.TYPE.FINDER;
  static engine = Config.ENGINES.EXPARSER;
  static fileExtension = "csv";
  static mimeType = "text/plain"

  constructor(content, fileName) {
    while (content.match(/\n\n/)) {
      content = content.replace(/\n\n/g, "\n");
    }
    super(content, fileName);
    this.textContent = [];
    this.layoutInfo = [];
    this.numPages = 0;
    let lines = this.content
      .split('\n')
      .map(line => line.trim());
    let yval = 0;
    for (let i = 0; i < lines.length; i++) {
      let line = lines[i]
      // we have layout info in the file, remove from text to re-add later
      let line_parts = line.split('\t');
      if (line_parts.length >= 7) {
        let layout_info = line_parts.slice(-6);
        let text_content = line_parts.slice(0, -6).join(' ');
        this.layoutInfo[i] = layout_info.join('\t');
        this.textContent[i] = text_content;
        let lineYval = layout_info[1];
        if (yval === 0 || yval - lineYval > 300) {
          this.numPages++;
          line = `<div class="page-marker" data-page="${this.numPages}"></div>` + this.textContent[i];
        }
        yval = lineYval;
      }
      this.textContent[i] = line;
    }
    this.content = this.textContent.join("\n")
  }

  toHtml() {
    return this._markupToHtml(content);
  }

  /**
   * @inheritDoc
   */
  loadFromHtml(html) {
    let markedUpText = super.loadFromHtml(html)
    // remove empty lines and nodes
    while (markedUpText.match(/\n\n/)) {
      markedUpText = markedUpText.replace(/\n\n/g, "\n")
    }
    markedUpText = markedUpText.replace(Config.REGEX.EMPTY_NODE, "")
    this.content = Annotation.removeXmlEntities(markedUpText)
    return this.content
  }

  toMarkup() {
    return super.toMarkup();
  }

  export() {
    let markedUpText = this.content;
    if (this.content.split("\n").length !== this.layoutInfo.length) {
      alert("Number of lines in document has changed, cannot export with layout info");
      return this.toMarkup()
    }
    let t1 = markedUpText.split('\n')
    let t2 = [];
    let rowFirstColumn;
    let allFirstColumns = "";
    for (let i = 0; i < t1.length; i++) {
      rowFirstColumn = t1[i];
      allFirstColumns = allFirstColumns + rowFirstColumn;
      if (i === t1.length - 1) {
        // no \n for last line
        if (typeof this.layoutInfo[i] != 'undefined') {
          t2[i] = t1[i] + '\t' + this.layoutInfo[i];
        } else {
          t2[i] = t1[i] + '\n'
        }
      } else {
        if (typeof this.layoutInfo[i] != 'undefined') {
          t2[i] = t1[i] + '\t' + this.layoutInfo[i] + '\n';
        } else {
          t2[i] = t1[i] + '\n'
        }
      }
      markedUpText = t2.join("");
    }
    return markedUpText
  }

  extractReferences() {
    throw new Error("Not implemented")
    return this.getContent()
  }

  toParserAnnotation() {
    return new AnystyleParserAnnotation(this.extractReferences(), this.getFileName().replace(/.ttx/, ".xml"))
  }

  toFinderAnnotation() {
    return this;
  }
}

class ExparserSegmentationAnnotation extends ParserAnnotation {
  static type = Annotation.TYPE.PARSER;
  static fileExtension = "xml";
  static mimeType = "text/xml"

  constructor(content, fileName) {
    while (content.match(/\n\n/)) {
      content = content.replace(/\n\n/g, "\n");
    }
    if (content.startsWith("<?xml")) {
      let textLines = content.split("\n");
      // remove root node
      textLines.splice(0, 2);
      textLines.splice(-1, 1);
      // remove enclosing <ref> and <author> tags
      textLines = textLines
        .map(line => line
          .replace(/<\/?author>/g, '')
          .replace(/<\/?ref>/g, ''));
      content = textLines.join("\n");
    }
    super(content, fileName);
    this.numRefs = content.split("\n").length

  }


  toMarkup() {
    return super.toMarkup();
  }

  export() {
    let textToExport = this.content.split("\n")
      .map(line => this.addAuthorTag(line))
      .map(line => `<ref>${line}</ref>`)
      .join("\n")
      .replace(/&/g, "&amp;")
    return `<?xml version="1.0" encoding="utf-8"?>\n<seganno>\n${textToExport}\n</seganno>`
  }

  /**
   * Returns a CSL representation of the annotation
   * @returns {[]}
   */
  static toCslJson() {

    function extract(tagName, text) {
      let regexp = new RegExp(`<${tagName}>(.*?)</${tagName}>`, "g");
      let m;
      let result = [];
      while (m = regexp.exec(text)) {
        result.push(m[1])
      }
      return result.length ? result : undefined;
    }

    function translate(ref) {
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
    return this.getContent().split("\n").map(ref => translate(ref));
  }


  addAuthorTag(markedUpText) {
    let startTag = "<author>";
    let endTag = "</author>";
    let firstStartTagMatch = null;
    let secondStartTagMatch = null;
    let lastEndTagMatch = null;
    let offset = 0;
    let matches = markedUpText.matchAll(/<\/?([^>]+)>/g);
    let pos;
    for (let match of matches) {
      let [tag, tagName] = match;
      if (["surname", "given-names"].includes(tagName)) {
        if (!tag.startsWith("</")) {
          // opening tag
          if (firstStartTagMatch === null) {
            // insert <author> before opening first surname or given-names
            firstStartTagMatch = match;
            pos = match.index + offset;
            markedUpText = markedUpText.substr(0, pos) + startTag + markedUpText.substr(pos);
            offset += startTag.length;
            //console.log({info: "inserting <author> before first tag", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch})
            continue;
          }
          if (secondStartTagMatch === null) {
            if (tag !== firstStartTagMatch[0]) {
              // if the second opening tag is not the same as the first, remember it and go on
              secondStartTagMatch = match;
              //console.log({info: "second opening tag not the same as the first", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch})
              continue;
            }
            // tag repeats
            //console.log("tag repeats")
          }
        } else {
          // closing tag
          lastEndTagMatch = match;
          if (!secondStartTagMatch || tagName !== secondStartTagMatch[1]) {
            //console.log({info: "Closing tag", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch});
            continue;
          }
        }
        if (lastEndTagMatch) {
          // insert </author> after the last closing tag
          pos = lastEndTagMatch.index + offset + lastEndTagMatch[0].length;
          markedUpText = markedUpText.substr(0, pos) + endTag + markedUpText.substr(pos);
          offset += endTag.length;
        }
        if (!tag.startsWith("</")) {
          // insert new opening tag
          //console.log({info:"Insert new opening tag", tag, firstStartTagMatch, secondStartTagMatch, lastEndTagMatch})
          pos = match.index + offset;
          markedUpText = markedUpText.substr(0, pos) + startTag + markedUpText.substr(pos);
          offset += startTag.length;
        }
        // reset matches
        firstStartTagMatch = null;
        secondStartTagMatch = null;
        lastEndTagMatch = null;
      }
    }
    if (lastEndTagMatch) {
      // insert missing closing tag
      pos = lastEndTagMatch.index + offset + lastEndTagMatch[0].length;
      markedUpText = markedUpText.substr(0, pos) + endTag + markedUpText.substr(pos);
    }
    return markedUpText;
  }

}

